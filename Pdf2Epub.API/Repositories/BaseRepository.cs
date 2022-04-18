using Microsoft.Data.Sqlite;
using SqlSugar;
using System.Linq.Expressions;

namespace Pdf2Epub.API.Repositories
{
    public class BaseRepository
    {
        private readonly SqlSugarClient db_;

        public BaseRepository()
        {
            var path = Path.Combine(Environment.CurrentDirectory, "backend.db");
            db_ = new SqlSugarClient(
                new ConnectionConfig() {
                    ConnectionString = new SqliteConnectionStringBuilder() {
                        DataSource = path,
                        Mode = SqliteOpenMode.ReadWriteCreate,
                    }.ToString(),
                    DbType = DbType.Sqlite,
                    IsAutoCloseConnection = true
                }
            );

        }

        internal ISqlSugarClient db
        {
            get
            {
                return db_;
            }
        }
    }

    public class BaseRepository<T> : BaseRepository where T : class, new()
    {
        public async Task<T> Add(T entity)
        {
            return await db.Insertable(entity).ExecuteReturnEntityAsync();
        }

        public async Task<bool> Update(T entity)
        {
            return await db.Updateable(entity).ExecuteCommandHasChangeAsync();
        }

        public async Task<List<T>> Query(Expression<Func<T, bool>> where_expression)
        {
            return await
                db
                .Queryable<T>()
                .WhereIF(where_expression != null, where_expression)
                .ToListAsync();
        }
    }
}
