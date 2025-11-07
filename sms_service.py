"""
SMS Service for sending news summaries via Twilio
Includes retry logic with exponential backoff
"""

import os
import time
import logging
from typing import List, Dict, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class SMSService:
    """Handle SMS sending with Twilio, including retry logic"""

    def __init__(
        self,
        account_sid: str = None,
        auth_token: str = None,
        from_number: str = None,
        dry_run: bool = False,
        sms_mode: str = None
    ):
        """
        Initialize Twilio client

        Args:
            account_sid: Twilio Account SID (defaults to env var)
            auth_token: Twilio Auth Token (defaults to env var)
            from_number: Twilio phone number (defaults to env var)
            dry_run: If True, simulate SMS sending without actually sending (test mode)
            sms_mode: SMS splitting mode - "segment" (120 chars) or "long" (1600 chars)
                     Defaults to env var SMS_MODE or "segment"
        """
        self.dry_run = dry_run
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_PHONE_NUMBER')

        # Configure SMS mode
        self.sms_mode = (sms_mode or os.getenv('SMS_MODE', 'segment')).lower()
        if self.sms_mode not in ['segment', 'long']:
            raise ValueError(f"Invalid SMS_MODE: {self.sms_mode}. Use 'segment' or 'long'")

        # Set max length based on mode
        self.max_length = 120 if self.sms_mode == 'segment' else 1600
        logger.info(f"SMS Service initialized with mode: {self.sms_mode} (max length: {self.max_length} chars)")

        # In dry-run mode, we don't need real credentials
        if not dry_run:
            if not all([self.account_sid, self.auth_token, self.from_number]):
                raise ValueError("Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER")
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.info("SMS Service initialized in DRY-RUN mode - no messages will be sent")

    def send_sms(
        self,
        to_number: str,
        message: str,
        max_retries: int = 5,
        initial_delay: float = 1.0
    ) -> Dict[str, any]:
        """
        Send SMS with exponential backoff retry logic
        Automatically splits long messages based on SMS mode

        Args:
            to_number: Recipient phone number
            message: Message text to send
            max_retries: Maximum number of retry attempts (default: 5)
            initial_delay: Initial delay in seconds before first retry (default: 1.0)

        Returns:
            Dict with status and details
        """
        # Check if message needs to be split
        if len(message) > self.max_length:
            logger.info(f"Message length ({len(message)} chars) exceeds limit ({self.max_length} chars). Splitting into segments...")
            chunks = self.split_long_message(message, self.max_length)
            logger.info(f"Split message into {len(chunks)} segments")

            # Send each chunk
            all_results = []
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"Sending segment {i}/{len(chunks)} to {to_number}")
                result = self._send_single_sms(to_number, chunk, max_retries, initial_delay)
                all_results.append(result)

                # If any part fails, return failure
                if not result["success"]:
                    logger.error(f"Failed to send segment {i}/{len(chunks)} to {to_number}")
                    return {
                        "success": False,
                        "to": to_number,
                        "error": f"Failed on segment {i}/{len(chunks)}",
                        "segments_sent": i - 1,
                        "total_segments": len(chunks),
                        "details": all_results
                    }

                # Wait 5 seconds before sending next segment (avoid rate limiting and ensure order)
                if i < len(chunks):
                    logger.debug(f"Waiting 5 seconds before sending next segment...")
                    time.sleep(5)

            # All parts sent successfully
            logger.info(f"Successfully sent all {len(chunks)} segments to {to_number}")
            return {
                "success": True,
                "to": to_number,
                "segments_sent": len(chunks),
                "total_segments": len(chunks),
                "sids": [r["sid"] for r in all_results],
                "details": all_results
            }

        # Message fits in single SMS
        return self._send_single_sms(to_number, message, max_retries, initial_delay)

    def _send_single_sms(
        self,
        to_number: str,
        message: str,
        max_retries: int = 5,
        initial_delay: float = 1.0
    ) -> Dict[str, any]:
        """
        Send a single SMS (internal method)

        Args:
            to_number: Recipient phone number
            message: Message text to send (must fit in one SMS)
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry

        Returns:
            Dict with status and details
        """
        # Dry-run mode: simulate successful send
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would send SMS to {to_number}")
            logger.info(f"[DRY-RUN] Message length: {len(message)} characters")
            logger.debug(f"[DRY-RUN] Message preview: {message[:100]}...")
            return {
                "success": True,
                "to": to_number,
                "sid": "DRY_RUN_SID",
                "status": "simulated",
                "attempts": 1,
                "dry_run": True
            }

        attempt = 0
        delay = initial_delay

        while attempt < max_retries:
            try:
                logger.info(f"Sending SMS to {to_number} (attempt {attempt + 1}/{max_retries})")

                # Send the message
                message_obj = self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )

                logger.info(f"SMS sent successfully to {to_number}. SID: {message_obj.sid}")

                return {
                    "success": True,
                    "to": to_number,
                    "sid": message_obj.sid,
                    "status": message_obj.status,
                    "attempts": attempt + 1
                }

            except TwilioRestException as e:
                attempt += 1
                logger.error(f"Twilio error sending to {to_number} (attempt {attempt}/{max_retries}): {e}")

                # Check if error is retryable
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error for {to_number}: {e.msg}")
                    return {
                        "success": False,
                        "to": to_number,
                        "error": str(e),
                        "error_code": e.code,
                        "attempts": attempt,
                        "retryable": False
                    }

                # If we have retries left, wait with exponential backoff
                if attempt < max_retries:
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

            except Exception as e:
                attempt += 1
                logger.error(f"Unexpected error sending to {to_number} (attempt {attempt}/{max_retries}): {e}")

                if attempt < max_retries:
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    delay *= 2

        # Max retries exceeded
        logger.error(f"Failed to send SMS to {to_number} after {max_retries} attempts")
        return {
            "success": False,
            "to": to_number,
            "error": "Max retries exceeded",
            "attempts": max_retries,
            "retryable": True
        }

    def _is_retryable_error(self, error: TwilioRestException) -> bool:
        """
        Determine if a Twilio error is retryable

        Args:
            error: TwilioRestException

        Returns:
            True if error should be retried, False otherwise
        """
        # Common non-retryable error codes
        non_retryable_codes = [
            21211,  # Invalid 'To' phone number
            21214,  # 'To' phone number cannot be reached
            21408,  # Permission to send an SMS has not been enabled
            21610,  # Attempt to send to unsubscribed recipient
        ]

        if error.code in non_retryable_codes:
            return False

        # Retryable errors include rate limiting, temporary service issues, etc.
        retryable_codes = [
            20429,  # Too many requests (rate limiting)
            20500,  # Internal server error
            20503,  # Service unavailable
        ]

        return error.code in retryable_codes or error.status >= 500

    def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        max_retries: int = 5
    ) -> Dict[str, any]:
        """
        Send SMS to multiple recipients

        Args:
            recipients: List of phone numbers
            message: Message text to send
            max_retries: Maximum retry attempts per recipient

        Returns:
            Dict with success/failure counts and details
        """
        results = {
            "total": len(recipients),
            "successful": 0,
            "failed": 0,
            "details": []
        }

        logger.info(f"Starting bulk SMS send to {len(recipients)} recipients")

        for phone_number in recipients:
            result = self.send_sms(phone_number, message, max_retries=max_retries)

            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["details"].append(result)

        logger.info(f"Bulk SMS complete: {results['successful']} sent, {results['failed']} failed")

        return results

    def split_long_message(self, message: str, max_length: int) -> List[str]:
        """
        Split long messages into SMS segments at word boundaries

        Args:
            message: Long message text
            max_length: Maximum length per segment

        Returns:
            List of message segments
        """
        if len(message) <= max_length:
            return [message]

        # Reserve space for "[XXX/YYY] " prefix
        # For up to 999 parts: "[123/456] " = 11 chars
        # Use 11 to be safe
        effective_max_length = max_length - 11

        chunks = []
        current_chunk = ""

        # Split by words to avoid breaking mid-word
        words = message.split(' ')

        for word in words:
            # If single word is longer than limit, we have to break it
            if len(word) > effective_max_length:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # Split long word into chunks
                for i in range(0, len(word), effective_max_length):
                    chunks.append(word[i:i + effective_max_length])
                continue

            # Check if adding this word exceeds the limit
            test_chunk = current_chunk + ' ' + word if current_chunk else word

            if len(test_chunk) <= effective_max_length:
                current_chunk = test_chunk
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word

        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Add part numbers if split into multiple segments
        # Format: [1/20] content here
        if len(chunks) > 1:
            chunks = [f"[{i+1}/{len(chunks)}] {chunk}" for i, chunk in enumerate(chunks)]

        return chunks
