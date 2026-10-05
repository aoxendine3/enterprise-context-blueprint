#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdatomic.h>
#include <pthread.h>
#include <sys/time.h>

#define DAG_CAPACITY 10000000ULL
#define NUM_AGENTS 10
#define NUM_LIARS 3

typedef struct {
    uint32_t node_id;
    uint64_t payload;
    uint64_t hash;
    atomic_int quarantined;
} DAG_Node;

DAG_Node* dag_memory;
atomic_size_t next_node_idx = 0;
atomic_size_t quarantined_count = 0;

uint64_t fnv1a_hash(uint64_t data) {
    uint64_t hash = 14695981039346656037ULL;
    uint8_t* p = (uint8_t*)&data;
    for(int i=0; i<8; i++) {
        hash ^= p[i];
        hash *= 1099511628211ULL;
    }
    return hash;
}

void* agent_worker(void* arg) {
    int agent_id = *(int*)arg;
    int is_liar = (agent_id <= NUM_LIARS); 
    
    while (1) {
        size_t idx = atomic_fetch_add(&next_node_idx, 1);
        if (idx >= DAG_CAPACITY) break;
        
        dag_memory[idx].node_id = agent_id;
        dag_memory[idx].payload = idx * 0x1A2B3C;
        
        if (is_liar) {
            dag_memory[idx].hash = 0xDEADBEEF; 
        } else {
            dag_memory[idx].hash = fnv1a_hash(dag_memory[idx].payload);
        }
        
        if (idx > 0) {
            uint64_t expected_hash = fnv1a_hash(dag_memory[idx-1].payload);
            if (dag_memory[idx-1].hash != expected_hash) {
                int expected = 0;
                if (atomic_compare_exchange_strong(&dag_memory[idx-1].quarantined, &expected, 1)) {
                    atomic_fetch_add(&quarantined_count, 1);
                }
            }
        }
    }
    return NULL;
}

int main() {
    size_t file_size = DAG_CAPACITY * sizeof(DAG_Node);
    const char* file_path = "dag_adversarial_matrix.bin";
    int fd = open(file_path, O_CREAT | O_RDWR, 0666);
    ftruncate(fd, file_size);
    #ifdef F_NOCACHE
    fcntl(fd, F_NOCACHE, 1);
    #endif

    dag_memory = mmap(NULL, file_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    
    pthread_t threads[NUM_AGENTS];
    int thread_ids[NUM_AGENTS];
    struct timeval start, end;
    gettimeofday(&start, NULL);

    for (int i = 0; i < NUM_AGENTS; i++) {
        thread_ids[i] = i + 1;
        pthread_create(&threads[i], NULL, agent_worker, &thread_ids[i]);
    }

    for (int i = 0; i < NUM_AGENTS; i++) {
        pthread_join(threads[i], NULL);
    }

    gettimeofday(&end, NULL);
    munmap(dag_memory, file_size);
    close(fd);
    
    double elapsed_s = (end.tv_sec - start.tv_sec) + (end.tv_usec - start.tv_usec) / 1000000.0;
    double tps = DAG_CAPACITY / elapsed_s;

    printf("ELAPSED:%.4f\n", elapsed_s);
    printf("TPS:%.0f\n", tps);
    printf("CAUGHT:%zu\n", (size_t)quarantined_count);
    return 0;
}
