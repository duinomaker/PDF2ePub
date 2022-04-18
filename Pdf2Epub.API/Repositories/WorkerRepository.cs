using Pdf2Epub.API.Models;

namespace Pdf2Epub.API.Repositories
{
    public class WorkerRepository : BaseRepository<WorkerModel>
    {
        public async Task<Guid> NewWorker()
        {
            return (
                await Add(
                    new WorkerModel() {
                        id = Guid.NewGuid(),
                        connect_time = DateTime.Now,
                        waiting = true,
                    }
                )
            ).id;
        }

        public async Task<List<Guid>> GetOnlineWorkerList()
        {
            return (
                await Query(
                    x => x.disconnect_time == null
                )
            ).Select(x => x.id).ToList();
        }

        public async Task<List<Guid>> GeAvailableWorkerList()
        {
            return (
                await Query(
                    x => x.disconnect_time == null
                    && x.waiting == true
                )
            ).Select(x => x.id).ToList();
        }

        public async Task<bool> SetWorkerWaiting(Guid id, bool waiting)
        {
            return await Update(
                new WorkerModel() {
                    id = id,
                    waiting = waiting
                }
            );
        }
    }
}
