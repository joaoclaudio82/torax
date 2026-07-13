import io

import numpy as np
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage

from imaging import load_image_with_metadata


def make_dicom() -> bytes:
    file_meta = Dataset()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = "1.2.826.0.1.3680043.8.498.1"

    dataset = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.Modality = "DX"
    dataset.ViewPosition = "PA"
    dataset.BodyPartExamined = "CHEST"
    dataset.PatientName = "Sensitive^Name"
    dataset.PatientID = "secret-id"
    dataset.Rows = 2
    dataset.Columns = 2
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 12
    dataset.HighBit = 11
    dataset.PixelRepresentation = 0
    dataset.RescaleSlope = 1
    dataset.RescaleIntercept = 0
    dataset.WindowCenter = 500
    dataset.WindowWidth = 400
    dataset.PixelData = np.array(
        [[0, 100], [500, 1000]],
        dtype=np.uint16,
    ).tobytes()

    buffer = io.BytesIO()
    dataset.save_as(buffer, enforce_file_format=True)
    return buffer.getvalue()


def test_dicom_applies_window_and_exposes_only_safe_metadata():
    image, metadata = load_image_with_metadata(make_dicom(), "study.dcm")

    assert image.min() == 300
    assert image.max() == 700
    assert metadata["format"] == "DICOM"
    assert metadata["view_position"] == "PA"
    assert metadata["body_part_examined"] == "CHEST"
    assert metadata["window_applied"] is True
    assert metadata["window_center"] == 500
    assert metadata["window_width"] == 400
    assert metadata["anonymized"] is True
    assert "PatientName" not in metadata
    assert "PatientID" not in metadata
