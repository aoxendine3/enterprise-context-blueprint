#include "xoras_ring_buffer.hpp"
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <iostream>
#include <stdexcept>

namespace xoras {

// Target capacity: 2^18 = 262,144 signals
// Each signal is 64 bytes.
// Total buffer size: ~16.7 MB
constexpr size_t BUFFER_CAPACITY = 262144;
constexpr const char* SHM_NAME = "/xoras_hft_ring_buffer";

class SHMManager {
public:
    SPSCRingBuffer<BUFFER_CAPACITY>* ring_buffer;
    int shm_fd;
    size_t shm_size;
    bool is_creator;

    SHMManager(bool create = false) : is_creator(create) {
        shm_size = sizeof(SPSCRingBuffer<BUFFER_CAPACITY>);

        if (create) {
            // Unlink any existing shared memory segment with the same name
            shm_unlink(SHM_NAME);
            
            // Create new shared memory segment
            shm_fd = shm_open(SHM_NAME, O_CREAT | O_RDWR | O_EXCL, 0666);
            if (shm_fd == -1) {
                throw std::runtime_error("Failed to shm_open for writing.");
            }

            // Set the size of the shared memory
            if (ftruncate(shm_fd, shm_size) == -1) {
                throw std::runtime_error("Failed to ftruncate shared memory.");
            }
        } else {
            // Open existing shared memory segment
            shm_fd = shm_open(SHM_NAME, O_RDWR, 0666);
            if (shm_fd == -1) {
                throw std::runtime_error("Failed to shm_open for reading.");
            }
        }

        // Map the shared memory into this process's address space
        void* ptr = mmap(0, shm_size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
        if (ptr == MAP_FAILED) {
            throw std::runtime_error("Failed to mmap shared memory.");
        }

        ring_buffer = new (ptr) SPSCRingBuffer<BUFFER_CAPACITY>();
    }

    ~SHMManager() {
        if (ring_buffer != nullptr) {
            munmap(ring_buffer, shm_size);
        }
        if (shm_fd != -1) {
            close(shm_fd);
        }
        if (is_creator) {
            shm_unlink(SHM_NAME);
        }
    }
};

} // namespace xoras
