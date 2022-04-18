using Microsoft.AspNetCore.SignalR;
using Pdf2Epub.API.Hubs;
using Pdf2Epub.API.Repositories;

namespace Pdf2Epub.API.Services
{
    public class WorkerService
    {
        private readonly WorkerRepository worker_repository_;
        private readonly IHubContext<MessageHub> hub_context_;


        public WorkerService(WorkerRepository worker_repository, IHubContext<MessageHub> hub_context)
        {
            worker_repository_ = worker_repository;
            hub_context_ = hub_context;
        }

        public async Task<Guid> RegisterWorker()
        {
            return await worker_repository_.NewWorker();
        }

        public async Task<int> GetOnlineWorkerCount()
        {
            return (await worker_repository_.GetOnlineWorkerList()).Count;
        }

        public async Task SendTaskToAllWorker(Guid task_id)
        {
            await hub_context_.Clients.All.SendAsync("ReceiveMessage", task_id);
        }

        public async Task<bool> SetWorkerWaiting(Guid id, bool waiting)
        {
            return await worker_repository_.SetWorkerWaiting(id, waiting);
        }
    }
}
