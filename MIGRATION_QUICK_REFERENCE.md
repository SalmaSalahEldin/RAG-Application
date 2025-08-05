# Migration Quick Reference

## 🚀 Quick Commands

### Check Migration Status
```bash
./check_migrations.sh
```

### Run All Migrations
```bash
./run_migrations.sh
```

### Manual Migration Commands
```bash
cd src/models/db_schemes/minirag
source ../../../venv/bin/activate

# Check current status
alembic current

# Apply all migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one step
alembic downgrade -1
```

## 📊 Current Migration Status

- **Current Revision**: `17c397cbdf9b (head)` (mergepoint)
- **Database**: PostgreSQL (`minirag`)
- **Tables**: 6 tables (users, projects, assets, chunks, query_logs, alembic_version)
- **User Isolation**: ✅ Implemented with `project_code` field

## 🔧 Common Issues & Solutions

### Issue: "command not found: alembic"
**Solution**: Activate virtual environment
```bash
cd src/models/db_schemes/minirag
source ../../../venv/bin/activate
```

### Issue: "column does not exist"
**Solution**: Apply migrations in order
```bash
alembic upgrade fee4cd54bd38        # Initial commit
alembic upgrade add_auth_tables     # Auth tables  
alembic upgrade add_project_code    # Project code
alembic upgrade head                # Merge heads
```

### Issue: "Multiple head revisions"
**Solution**: Merge heads
```bash
alembic heads
alembic merge -m "merge heads" <head1> <head2>
alembic upgrade head
```

## 📁 Migration Files

- `fee4cd54bd38_initial_commit.py` - Initial database schema
- `add_auth_tables.py` - User authentication tables
- `add_project_code.py` - User-scoped project IDs
- `17c397cbdf9b_merge_heads.py` - Merge migration

## 🎯 Key Features

- ✅ **User Authentication**: JWT-based auth with user table
- ✅ **User Isolation**: Each user has isolated document spaces
- ✅ **Project Management**: User-scoped project IDs (Project 1, 2, 3 per user)
- ✅ **Query Logging**: Stores timestamp, user ID, response time, question, LLM response
- ✅ **Document Processing**: File upload, chunking, vector storage
- ✅ **Vector Search**: Qdrant integration for similarity search

---

**📖 Full Guide**: See `MIGRATION_GUIDE.md` for detailed documentation. 