from app.core.form_schema import FieldDefinition


def test_bbox_ratio_validation():
    f = FieldDefinition(
        field_id="F001",
        standard_name="t",
        label="l",
        page_no=1,
        bbox_ratio=[0.1, 0.2, 0.5, 0.6],
        field_type="text",
    )
    f.validate()


def test_bbox_pixels_logic():
    bbox = [0.0, 0.0, 0.5, 0.5]
    w, h = 1000, 2000
    x0, y0, x1, y1 = (
        int(bbox[0] * w),
        int(bbox[1] * h),
        int(bbox[2] * w),
        int(bbox[3] * h),
    )
    assert (x0, y0, x1, y1) == (0, 0, 500, 1000)
