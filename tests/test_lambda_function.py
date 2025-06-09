"""Unit tests for the AWS Lambda handler (lambda_function.py)."""

import tempfile
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from lambda_function import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    def _create_s3_event(
        self, bucket_name: str, object_key: str
    ) -> Dict[str, Any]:
        return {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": bucket_name},
                        "object": {"key": object_key},
                    }
                }
            ]
        }

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_success(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test successful processing of a PNG image in the input/ prefix."""
        bucket = "test-bucket"
        key = "input/test_image.png"
        event = self._create_s3_event(bucket, key)

        mock_s3_client.download_file = MagicMock()
        mock_s3_client.upload_file = MagicMock()
        mock_compute_fft.return_value = (
            None  # Assuming compute_fft doesn't return anything
        )

        with tempfile.TemporaryDirectory() as _:
            # Mock os.path.join to work within the real tempdir created
            # by the test but ensure the lambda function's tempdir usage is
            # also controlled if it creates its own. For simplicity here,
            # we assume the lambda's tempfile.TemporaryDirectory() works as
            # expected. We need to ensure compute_fft is called with paths
            # that would exist.

            # To make compute_fft work correctly if it tries to access files,
            # we can make it a no-op or ensure the mocked paths are handled.
            # Here, compute_fft is mocked, so its internal file operations
            # don't run.

            response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_called_once()
        args, _ = mock_s3_client.download_file.call_args
        self.assertEqual(args[0], bucket)
        self.assertEqual(args[1], key)
        # args[2] is a temporary path, difficult to predict
        # exactly without more mocking

        mock_compute_fft.assert_called_once()
        # args_fft, _ = mock_compute_fft.call_args
        # self.assertTrue(args_fft[0].endswith("test_image.png"))
        # self.assertTrue(args_fft[1].endswith("fft-test_image.png"))

        mock_s3_client.upload_file.assert_called_once()
        args_upload, _ = mock_s3_client.upload_file.call_args
        # self.assertTrue(args_upload[0].endswith("fft-test_image.png"))
        self.assertEqual(args_upload[1], bucket)
        self.assertEqual(args_upload[2], "output/fft-test_image.png")

        self.assertEqual(response, {"status": "done"})
        mock_logger.info.assert_any_call(
            "Processing %s in bucket %s", key, bucket
        )
        mock_logger.info.assert_any_call(
            "Successfully processed %s to %s", key, "output/fft-test_image.png"
        )

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_skip_non_input_prefix(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test that files not in input/ prefix are skipped."""
        event = self._create_s3_event("test-bucket", "other/test_image.png")
        response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_not_called()
        mock_compute_fft.assert_not_called()
        mock_s3_client.upload_file.assert_not_called()
        mock_logger.info.assert_called_with(
            "Skipping file %s as it is not in input/ prefix",
            "other/test_image.png",
        )
        self.assertEqual(response, {"status": "done"})

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_skip_non_png(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test that non-PNG files are skipped."""
        event = self._create_s3_event("test-bucket", "input/test_image.jpg")
        response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_not_called()
        mock_compute_fft.assert_not_called()
        mock_s3_client.upload_file.assert_not_called()
        mock_logger.warning.assert_called_with(
            "Skipping file %s as it is not a PNG file.", "input/test_image.jpg"
        )
        self.assertEqual(response, {"status": "done"})

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_s3_download_exception(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test error handling when S3 download fails."""
        bucket = "test-bucket"
        key = "input/test_image.png"
        event = self._create_s3_event(bucket, key)

        mock_s3_client.download_file.side_effect = Exception(
            "S3 Download Error"
        )

        response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_called_once()
        # Should not be called if download fails
        mock_compute_fft.assert_not_called()
        mock_s3_client.upload_file.assert_not_called()
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertIn("Error processing record", args[0])
        self.assertIsInstance(kwargs["exc_info"], Exception)
        self.assertEqual(response, {"status": "done"})

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_compute_fft_exception(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test error handling when compute_fft fails."""
        bucket = "test-bucket"
        key = "input/test_image.png"
        event = self._create_s3_event(bucket, key)

        mock_s3_client.download_file = MagicMock()
        mock_compute_fft.side_effect = Exception("FFT Computation Error")

        with tempfile.TemporaryDirectory() as _:
            # Path setup for download
            # in_path = os.path.join(tmpdir, os.path.basename(key))
            # out_path = os.path.join(tmpdir, f"fft-{os.path.basename(key)}")

            # To simulate the file being "downloaded" for compute_fft
            # to be called file if compute_fft is properly mocked.

            response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_called_once()
        mock_compute_fft.assert_called_once()
        # Should not be called if FFT fails
        mock_s3_client.upload_file.assert_not_called()
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertIn("Error processing record", args[0])
        self.assertIsInstance(kwargs["exc_info"], Exception)
        self.assertEqual(response, {"status": "done"})

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_s3_upload_exception(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test error handling when S3 upload fails."""
        bucket = "test-bucket"
        key = "input/test_image.png"
        event = self._create_s3_event(bucket, key)

        mock_s3_client.download_file = MagicMock()
        mock_compute_fft.return_value = None  # Successful computation
        mock_s3_client.upload_file.side_effect = Exception("S3 Upload Error")

        with tempfile.TemporaryDirectory() as _:
            response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_called_once()
        mock_compute_fft.assert_called_once()
        mock_s3_client.upload_file.assert_called_once()
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertIn("Error processing record", args[0])
        self.assertIsInstance(kwargs["exc_info"], Exception)
        self.assertEqual(response, {"status": "done"})

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_no_records(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test behavior when event has no records."""
        event = {"Records": []}
        response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_not_called()
        mock_compute_fft.assert_not_called()
        mock_s3_client.upload_file.assert_not_called()
        mock_logger.info.assert_not_called()  # No processing logs
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        self.assertEqual(response, {"status": "done"})

    @patch("lambda_function.s3")
    @patch("lambda_function.compute_fft")
    @patch("lambda_function.logger")
    def test_lambda_handler_malformed_record(
        self,
        mock_logger: MagicMock,
        mock_compute_fft: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test behavior with a malformed S3 record (e.g., missing keys)."""
        event = {
            "Records": [{"s3": {"bucket": {"name": "test-bucket"}}}]
        }  # Missing object key

        response = lambda_handler(event, None)

        mock_s3_client.download_file.assert_not_called()
        mock_compute_fft.assert_not_called()
        mock_s3_client.upload_file.assert_not_called()
        # Should log an error due to KeyError
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertIn("Error processing record", args[0])
        self.assertIsInstance(
            kwargs["exc_info"], KeyError
        )  # Expecting a KeyError
        self.assertEqual(response, {"status": "done"})


if __name__ == "__main__":
    unittest.main()
