namespace Pdf2Epub.API.Models
{
    public enum ConvertStatus
    {
        UPLOADING,
        UPLOAD_FAILED,
        DISTRIBUTING,
        DISTRIBUTION_FAILED,
        CONVERTION_PENDING,
        CONVERTING,
        CONVERTION_SUCCEED,
        CONVERTION_FAILED,
    }
}
