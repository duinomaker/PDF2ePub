using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Pdf2Epub.API.Repositories;
using Pdf2Epub.API.Services;

namespace Pdf2Epub.API.Controllers
{
    [Route("worker")]
    [ApiController]
    public class WorkerController : ControllerBase
    {
        private readonly WorkerService worker_service_;
        private readonly ConvertTaskRepository convert_task_repository_;

        public WorkerController(WorkerService worker_service, ConvertTaskRepository convert_task_repository)
        {
            worker_service_ = worker_service;
            convert_task_repository_ = convert_task_repository;
        }

        [HttpPost]
        public async Task<IActionResult> Register()
        {
            return Ok(await worker_service_.RegisterWorker());
        }

        [HttpPost("{worker_id}/{task_id}")]
        public async Task<IActionResult> ClaimTask([FromRoute] Guid worker_id, [FromRoute] Guid task_id)
        {
            if (await convert_task_repository_.GetTaskStatus(task_id) != Models.ConvertStatus.UPLOADING)
            {
                return NoContent();
            }

            convert_task_repository_.UpdateTaskState(task_id, Models.ConvertStatus.DISTRIBUTING);
            convert_task_repository_.UpdateWorkerId(task_id, worker_id);
            worker_service_.SetWorkerWaiting(worker_id, false);

            return Ok(await convert_task_repository_.GetTaskFilename(task_id));
        }
    }
}
