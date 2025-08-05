# Database Migration Guide

This guide explains how to handle database migrations in the RAG project using Alembic.

## 📋 Table of Contents

- [Overview](#overview)
- [Migration Structure](#migration-structure)
- [Common Migration Commands](#common-migration-commands)
- [Migration Workflow](#migration-workflow)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## 🎯 Overview

The RAG project uses **Alembic** for database migrations, which is the migration tool for SQLAlchemy. Migrations are stored in `src/models/db_schemes/minirag/alembic/`.

### Key Components

- **Alembic Configuration**: `src/models/db_schemes/minirag/alembic.ini`
- **Migration Scripts**: `src/models/db_schemes/minirag/alembic/versions/`
- **Environment**: `src/models/db_schemes/minirag/alembic/env.py`
- **Database URL**: Configured in environment variables

## 🏗️ Migration Structure

```
src/models/db_schemes/minirag/
├── alembic/
│   ├── versions/                    # Migration files
│   │   ├── fee4cd54bd38_initial_commit.py
│   │   ├── add_auth_tables.py
│   │   ├── add_project_code.py
│   │   └── 17c397cbdf9b_merge_heads.py
│   ├── env.py                       # Migration environment
│   └── script.py.mako              # Migration template
├── alembic.ini                      # Alembic configuration
└── schemes/                         # SQLAlchemy models
```

## 🛠️ Common Migration Commands

### Prerequisites

1. **Activate Virtual Environment**:
   ```bash
   cd src/models/db_schemes/minirag
   source ../../../venv/bin/activate
   ```

2. **Ensure Database Connection**:
   ```bash
   # Test PostgreSQL connection
   psql -h localhost -U postgres -d minirag -c "SELECT 'Connection successful' as status;"
   ```

### Basic Commands

#### Check Current Migration Status
```bash
alembic current
```
**Output**: Shows the current migration revision (e.g., `17c397cbdf9b (head)`)

#### View Migration History
```bash
alembic history
```
**Output**: Shows all migrations and their relationships

#### List All Migrations
```bash
alembic history --verbose
```

### Migration Operations

#### Apply All Pending Migrations
```bash
alembic upgrade head
```
**Use Case**: Apply all migrations to the latest version

#### Apply Specific Migration
```bash
alembic upgrade <revision_id>
```
**Example**:
```bash
alembic upgrade fee4cd54bd38        # Apply initial commit
alembic upgrade add_auth_tables     # Apply auth tables
alembic upgrade add_project_code    # Apply project code
```

#### Rollback to Previous Migration
```bash
alembic downgrade -1                # Rollback one step
alembic downgrade <revision_id>     # Rollback to specific revision
```

#### Check Migration Status
```bash
alembic show <revision_id>
```

### Creating New Migrations

#### Auto-Generate Migration
```bash
alembic revision --autogenerate -m "Description of changes"
```
**Example**:
```bash
alembic revision --autogenerate -m "Add new user fields"
```

#### Manual Migration
```bash
alembic revision -m "Description of changes"
```

## 🔄 Migration Workflow

### 1. Development Workflow

#### Step 1: Make Model Changes
Edit your SQLAlchemy models in `src/models/db_schemes/minirag/schemes/`

#### Step 2: Generate Migration
```bash
cd src/models/db_schemes/minirag
source ../../../venv/bin/activate
alembic revision --autogenerate -m "Description of changes"
```

#### Step 3: Review Migration
Check the generated migration file in `alembic/versions/`

#### Step 4: Apply Migration
```bash
alembic upgrade head
```

#### Step 5: Test
Verify the changes work as expected

### 2. Production Deployment

#### Step 1: Backup Database
```bash
pg_dump -h localhost -U postgres -d minirag > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### Step 2: Apply Migrations
```bash
cd src/models/db_schemes/minirag
source ../../../venv/bin/activate
alembic upgrade head
```

#### Step 3: Verify
```bash
alembic current
psql -h localhost -U postgres -d minirag -c "\dt"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "command not found: alembic"
**Problem**: Virtual environment not activated
**Solution**:
```bash
cd src/models/db_schemes/minirag
source ../../../venv/bin/activate
```

#### 2. "column does not exist" Error
**Problem**: Migration trying to reference non-existent column
**Solution**:
1. Check migration order
2. Apply migrations step by step:
   ```bash
   alembic upgrade fee4cd54bd38        # Initial commit
   alembic upgrade add_auth_tables     # Auth tables
   alembic upgrade add_project_code    # Project code
   alembic upgrade head                # Merge heads
   ```

#### 3. "Multiple head revisions" Error
**Problem**: Divergent migration branches
**Solution**:
```bash
# Check heads
alembic heads

# Merge heads
alembic merge -m "merge heads" <head1> <head2>

# Apply merged migration
alembic upgrade head
```

#### 4. Database Connection Issues
**Problem**: Cannot connect to PostgreSQL
**Solution**:
```bash
# Test connection
psql -h localhost -U postgres -d minirag -c "SELECT 1;"

# Check PostgreSQL service
sudo systemctl status postgresql

# Reset password if needed
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

#### 5. Migration Conflicts
**Problem**: Migration conflicts with existing data
**Solution**:
1. **Backup data**:
   ```bash
   pg_dump -h localhost -U postgres -d minirag > backup.sql
   ```

2. **Reset database** (if safe):
   ```bash
   dropdb -h localhost -U postgres minirag
   createdb -h localhost -U postgres minirag
   ```

3. **Reapply migrations**:
   ```bash
   alembic upgrade head
   ```

### Emergency Recovery

#### Reset All Migrations
```bash
# Drop and recreate database
dropdb -h localhost -U postgres minirag
createdb -h localhost -U postgres minirag

# Reapply all migrations
alembic upgrade head
```

#### Manual Migration Fix
```bash
# Mark current revision manually
alembic stamp head

# Or mark specific revision
alembic stamp <revision_id>
```

## 📊 Migration Status Commands

### Check Database Tables
```bash
psql -h localhost -U postgres -d minirag -c "\dt"
```

### Check Table Structure
```bash
psql -h localhost -U postgres -d minirag -c "\d table_name"
```

### Check Migration Version
```bash
psql -h localhost -U postgres -d minirag -c "SELECT * FROM alembic_version;"
```

## 🎯 Best Practices

### 1. Migration Naming
- Use descriptive names: `add_user_authentication.py`
- Include ticket/issue numbers: `add_user_authentication_issue_123.py`
- Use present tense: `add_` not `added_`

### 2. Migration Content
- **Always review** auto-generated migrations
- **Test migrations** on development database first
- **Include rollback logic** when possible
- **Document complex changes** in migration comments

### 3. Database Safety
- **Always backup** before applying migrations
- **Test migrations** on staging environment
- **Monitor migration execution** in production
- **Have rollback plan** ready

### 4. Team Collaboration
- **Commit migrations** with model changes
- **Coordinate migrations** with team members
- **Document breaking changes**
- **Review migration files** in pull requests

## 🔧 Utility Scripts

### Quick Migration Script
Create `run_migrations.sh` in project root:
```bash
#!/bin/bash
echo "Running database migrations..."
cd src/models/db_schemes/minirag
source ../../../venv/bin/activate
alembic upgrade head
echo "Migrations completed!"
```

### Migration Status Check
Create `check_migrations.sh`:
```bash
#!/bin/bash
echo "Checking migration status..."
cd src/models/db_schemes/minirag
source ../../../venv/bin/activate
echo "Current migration:"
alembic current
echo ""
echo "Migration history:"
alembic history
```

## 📝 Example Migration Workflow

### Scenario: Adding User Profile Fields

1. **Update Model** (`schemes/user.py`):
   ```python
   class User(SQLAlchemyBase):
       # ... existing fields ...
       profile_picture = Column(String, nullable=True)
       bio = Column(Text, nullable=True)
   ```

2. **Generate Migration**:
   ```bash
   cd src/models/db_schemes/minirag
   source ../../../venv/bin/activate
   alembic revision --autogenerate -m "Add user profile fields"
   ```

3. **Review Migration** (`alembic/versions/xxx_add_user_profile_fields.py`):
   ```python
   def upgrade() -> None:
       op.add_column('users', sa.Column('profile_picture', sa.String(), nullable=True))
       op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))

   def downgrade() -> None:
       op.drop_column('users', 'bio')
       op.drop_column('users', 'profile_picture')
   ```

4. **Apply Migration**:
   ```bash
   alembic upgrade head
   ```

5. **Verify Changes**:
   ```bash
   psql -h localhost -U postgres -d minirag -c "\d users"
   ```

## 🆘 Getting Help

### Common Resources
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Project-Specific Help
- Check `src/models/db_schemes/minirag/alembic/env.py` for configuration
- Review existing migrations in `alembic/versions/`
- Check `schemes/` directory for model definitions

---

**⚠️ Important**: Always backup your database before applying migrations in production! 