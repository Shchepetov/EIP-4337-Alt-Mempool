// userOperation-cli/cli.go
package main

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"

	"golang.org/x/net/context"
	"google.golang.org/grpc"
	pb "mempool/mempool-service/proto"
)

const (
	address        = "localhost:50051"
	userOpFileName = "userop.json"
)

func parseFile(file string) (*pb.UserOperation, error) {
	var userOperation *pb.UserOperation
	data, err := ioutil.ReadFile(file)
	if err != nil {
		return nil, err
	}
	json.Unmarshal(data, &userOperation)

	return userOperation, err
}

func main() {
	conn, err := grpc.Dial(address, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Did not connect: %v", err)
	}
	defer conn.Close()
	client := pb.NewMemPoolClient(conn)

	file := userOpFileName
	if len(os.Args) > 1 {
		file = os.Args[1]
	}

	userOperation, err := parseFile(file)
	if err != nil {
		log.Fatalf("Could not parse file: %v", err)
	}

	r, err := client.Add(context.Background(), userOperation)
	if err != nil {
		log.Fatalf("Could not greet: %v", err)
	}
	log.Printf("Added: %t", r.Ok)

	getAll, err := client.GetAll(context.Background(), &pb.GetRequest{})
	if err != nil {
		log.Fatalf("Could not list user operations: %v", err)
	}
	for _, v := range getAll.UserOperations {
		log.Println(v)
	}
}
