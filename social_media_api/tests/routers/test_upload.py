import contextlib
import os
import pathlib
import tempfile
import pytest
from httpx import AsyncClient


@pytest.fixture
def sample_image(fs) -> pathlib.Path:
    path = (pathlib.Path(__file__).parent / "assets" / "sample_image.jpg").resolve()
    fs.create_file(path)
    return path


@pytest.fixture(autouse=True)
def mock_upload_file_to_b2(mocker):
    return mocker.patch(
        "social_media_api.routers.upload.upload_file_to_b2",
        return_value="https://fake-b2-url.com/sample_image.jpg",
    )


@pytest.fixture(autouse=True)
def aiofiles_mock_open(mocker, fs):
    mock_open = mocker.patch("aiofiles.open")

    @contextlib.asynccontextmanager
    async def async_file_open(fname: str, mode: str = "r"):
        out_fs_mock = mocker.AsyncMock(name=f"async_file_open:{fname!r}/{mode!r}")
        with open(fname, mode) as fin:
            out_fs_mock.read.side_effect = fin.read
            out_fs_mock.write.side_effect = fin.write
            yield out_fs_mock

    mock_open.side_effect = async_file_open
    return mock_open


async def call_upload_endpoint(
    async_client: AsyncClient, token: str, sample_image: pathlib.Path
):
    return await async_client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": open(sample_image, "rb")},
    )


@pytest.mark.anyio
async def test_upload_image(
    async_client: AsyncClient, logged_in_token: str, sample_image: pathlib.Path
):
    response = await call_upload_endpoint(async_client, logged_in_token, sample_image)
    assert response.status_code == 201
    assert "file_url" in response.json()
    assert response.json()["file_url"] == "https://fake-b2-url.com/sample_image.jpg"


@pytest.mark.anyio
async def test_temp_file_removed_after_upload(
    async_client: AsyncClient, logged_in_token: str, sample_image: pathlib.Path, mocker
):
    named_temp_file_spy = mocker.spy(tempfile, "NamedTemporaryFile")

    response = await call_upload_endpoint(async_client, logged_in_token, sample_image)
    assert response.status_code == 201

    created_temp_file = named_temp_file_spy.return_value
    assert not os.path.exists(created_temp_file.name), "Temporary file should be removed after upload"