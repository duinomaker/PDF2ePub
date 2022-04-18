using Pdf2Epub.API.Models;

namespace Pdf2Epub.API.Extensions
{
    public interface IWorkerHubClient
    {
        Task<List<Guid>> GetTaskList();

        Task<ConvertTaskModel> GetTaskStatus(Guid id);
    }
}
