package main

import (
	"encoding/hex"
	"fmt"
	"golang.org/x/crypto/sha3"
	"log"
	pb "mempool/mempool-service/proto"
	"mempool/mempool-service/sqlite"
	"net"

	"golang.org/x/net/context"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

const (
	port       = ":50051"
	dbFileName = "mempool.sqlite"
)

type service struct {
	repo *sqlite.SQLiteRepository
}

func (s *service) Add(
	ctx context.Context,
	req *pb.UserOperation,
) (*pb.Response, error) {
	if req.InitCode != "" {
		hash := sha3.New256()
		hash.Write([]byte(req.InitCode))
		hash.Write([]byte(req.Nonce))

		req.Sender = fmt.Sprintf("0x%s", hex.EncodeToString(hash.Sum(nil)[:20]))
	}
	userOperation, err := s.repo.InsertOrUpdate(req)
	if err != nil {
		return nil, err
	}
	return &pb.Response{Ok: true, UserOperation: userOperation}, nil
}

func (s *service) GetAll(
	ctx context.Context,
	req *pb.GetRequest,
) (*pb.Response, error) {
	userOperations, err := s.repo.GetAll()
	return &pb.Response{UserOperations: userOperations}, err
}

func main() {
	repo, err := sqlite.Open(dbFileName)
	if err != nil {
		log.Fatalf("failed to open db: %v", err)
	}

	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	s := grpc.NewServer()

	pb.RegisterMemPoolServer(s, &service{repo})

	reflection.Register(s)
	if err = s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
