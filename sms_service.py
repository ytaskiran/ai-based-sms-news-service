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

    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None, dry_run: bool = False):
        """
        Initialize Twilio client

        Args:
            account_sid: Twilio Account SID (defaults to env var)
            auth_token: Twilio Auth Token (defaults to env var)
            from_number: Twilio phone number (defaults to env var)
            dry_run: If True, simulate SMS sending without actually sending (test mode)
        """
        self.dry_run = dry_run
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_PHONE_NUMBER')

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

        Args:
            to_number: Recipient phone number
            message: Message text to send
            max_retries: Maximum number of retry attempts (default: 5)
            initial_delay: Initial delay in seconds before first retry (default: 1.0)

        Returns:
            Dict with status and details
        """
        # Dry-run mode: simulate successful send
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would send SMS to {to_number}")
            logger.info(f"[DRY-RUN] Message preview (first 200 chars): {message[:200]}...")
            logger.info(f"[DRY-RUN] Message length: {len(message)} characters")
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

    def split_long_message(self, message: str, max_length: int = 1600) -> List[str]:
        """
        Split long messages into SMS-friendly chunks

        Args:
            message: Long message text
            max_length: Maximum length per message (default: 1600 for MMS)

        Returns:
            List of message chunks
        """
        if len(message) <= max_length:
            return [message]

        chunks = []
        current_chunk = ""

        # Split by paragraphs first
        paragraphs = message.split('\n\n')

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_length:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'

        if current_chunk:
            chunks.append(current_chunk.strip())

        # Add part numbers if split into multiple messages
        if len(chunks) > 1:
            chunks = [f"[Part {i+1}/{len(chunks)}]\n{chunk}" for i, chunk in enumerate(chunks)]

        return chunks
