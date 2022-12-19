package sqlite

import (
	"database/sql"
	pb "mempool/mempool-service/proto"
	"modernc.org/sqlite"

	_ "modernc.org/sqlite"
	sqlite3 "modernc.org/sqlite/lib"
)

type SQLiteRepository struct {
	db *sql.DB
}

func NewSQLiteRepository(db *sql.DB) *SQLiteRepository {
	return &SQLiteRepository{
		db: db,
	}
}

func Open(dbFileName string) (*SQLiteRepository, error) {
	db, err := sql.Open("sqlite", dbFileName)
	if err != nil {
		return nil, err
	}

	r := NewSQLiteRepository(db)
	_, err = r.db.Exec(`
    CREATE TABLE IF NOT EXISTS userOperations(
        sender BYTE PRIMARY KEY NOT NULL,
        nonce BYTE NOT NULL,
        init_code BYTE
        );
    `)

	return r, err
}

func (r *SQLiteRepository) InsertOrUpdate(
	userOperation *pb.UserOperation,
) (*pb.UserOperation, error) {
	_, err := r.db.Exec(
		`INSERT INTO userOperations(sender, nonce, init_code) values(?,?,?)`,
		userOperation.Sender,
		userOperation.Nonce,
		userOperation.InitCode,
	)
	if liteErr, ok := err.(*sqlite.Error); ok {
		code := liteErr.Code()
		if code == sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY {
			_, err := r.db.Exec(
				`UPDATE userOperations SET nonce = ?, init_code = ? WHERE sender = ?`,
				userOperation.Nonce,
				userOperation.InitCode,
				userOperation.Sender,
			)
			if err != nil {
				return nil, err
			}
		}
	}

	return userOperation, nil
}

func (r *SQLiteRepository) GetAll() ([]*pb.UserOperation, error) {
	rows, err := r.db.Query(`SELECT * FROM userOperations`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var all []*pb.UserOperation
	for rows.Next() {
		var userOperation pb.UserOperation
		if err = rows.Scan(&userOperation.Sender, &userOperation.Nonce, &userOperation.InitCode); err != nil {
			return nil, err
		}
		all = append(all, &userOperation)
	}
	return all, nil
}
