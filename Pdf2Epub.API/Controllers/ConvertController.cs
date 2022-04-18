using Microsoft.AspNetCore.Mvc;
using Pdf2Epub.API.Models;
using Pdf2Epub.API.Repositories;
using Pdf2Epub.API.Services;

namespace Pdf2Epub.API.Controllers
{
    [Route("convert")]
    [ApiController]
    public class ConvertController : ControllerBase
    {
        private readonly ConvertTaskRepository convert_task_repository_;
        private readonly WorkerService worker_service_;

        public ConvertController(ConvertTaskRepository convert_task_repository, WorkerService worker_service)
        {
            convert_task_repository_ = convert_task_repository;
            worker_service_ = worker_service;
        }

        [HttpPost]
        public async Task<IActionResult> CreateTask([FromForm] string file_id)
        {
            var id = await convert_task_repository_.NewTask();

            convert_task_repository_.UpdateFileName(id, file_id);

            if (!System.IO.File.Exists($"/root/{file_id}"))
            {
                convert_task_repository_.UpdateTaskState(id, ConvertStatus.UPLOAD_FAILED);
                return NotFound();
            }

            worker_service_.SendTaskToAllWorker(id);

            return Ok(id);
        }
    }
}
