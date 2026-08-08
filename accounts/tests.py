from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.validators import validate_egyptian_phone


class EgyptianPhoneValidatorTest(TestCase):
    def test_valid_11_digit_phone_numbers(self):
        valid_numbers = [
            "01012345678",
            "01198765432",
            "01200000000",
            "01555555555",
            "+201012345678",
            "00201012345678",
            "010 1234 5678",
            "010-1234-5678",
        ]
        for number in valid_numbers:
            with self.subTest(number=number):
                try:
                    validate_egyptian_phone(number)
                except ValidationError:
                    self.fail(f"validate_egyptian_phone failed unexpectedly for valid input: {number}")

    def test_invalid_phone_numbers_raises_11_digit_error(self):
        invalid_numbers = [
            "0101234567",       # 10 digits
            "010123456789",     # 12 digits
            "01312345678",      # 013 is not a valid carrier prefix
            "abcdefghijk",      # letters
            "12345",            # too short
        ]
        for number in invalid_numbers:
            with self.subTest(number=number):
                with self.assertRaises(ValidationError) as cm:
                    validate_egyptian_phone(number)
                self.assertIn(
                    "Please enter a valid 11-digit Egyptian mobile number.",
                    cm.exception.messages,
                )
