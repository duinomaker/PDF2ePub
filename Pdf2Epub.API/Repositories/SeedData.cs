using System.Reflection;

namespace Pdf2Epub.API.Repositories
{
    public class SeedData
    {
        public static void Seed()
        {
            var repository = new BaseRepository();
            repository.db.DbMaintenance.CreateDatabase();

            //var assamblies = AppDomain.CurrentDomain.GetAssemblies();
            //foreach (Assembly assembly in assamblies)
            //{
            //    var types = assembly.GetTypes().Where(t => t.FullName?.StartsWith("Pdf2Epub.API.Models") ?? false).ToArray();
            //    repository.db.CodeFirst.InitTables(types);
            //}
            repository.db.CodeFirst.SetStringDefaultLength(200).InitTables(typeof(Pdf2Epub.API.Models.ConvertTaskModel));
            repository.db.CodeFirst.SetStringDefaultLength(200).InitTables(typeof(Pdf2Epub.API.Models.WorkerModel));
        }
    }
}
