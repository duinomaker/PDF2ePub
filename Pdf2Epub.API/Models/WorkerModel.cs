using SqlSugar;

namespace Pdf2Epub.API.Models
{
    public class WorkerModel
    {
        [SugarColumn(IsPrimaryKey = true)]
        public Guid id { get; set; }

        public DateTime connect_time { get; set; }

        public bool waiting { get; set; }

        [SugarColumn(IsNullable = true)]
        public DateTime? disconnect_time { get; set; }
    }
}
