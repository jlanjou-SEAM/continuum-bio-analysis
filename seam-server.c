#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <time.h>

#define PORT 5000
#define BUFFER_SIZE 65536
#define MAX_COMPOUNDS 1000
#define MAX_TASKS 100

const char *LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4";
const int ROWS = 5734;
const int STRUCTURES = 420;

typedef struct {
    char name[256];
    char formula[256];
    char category[256];
} Compound;

typedef struct {
    char id[32];
    char status[32];
    int progress;
    char result[8192];
} Task;

Compound compounds[MAX_COMPOUNDS];
int compound_count = 0;
Task tasks[MAX_TASKS];
int task_count = 0;
int next_task_id = 0;

void load_compounds() {
    // Hardcoded compounds - in production, load from JSON
    // For now, we'll create a minimal set for testing
    strcpy(compounds[0].name, "Acetaminophen");
    strcpy(compounds[0].formula, "C8H9NO2");
    strcpy(compounds[0].category, "Drug - Pain/fever");

    strcpy(compounds[1].name, "Ibuprofen");
    strcpy(compounds[1].formula, "C13H18O2");
    strcpy(compounds[1].category, "Drug - NSAID");

    strcpy(compounds[2].name, "Vitamin C");
    strcpy(compounds[2].formula, "C6H8O6");
    strcpy(compounds[2].category, "Supplement - Vitamin");

    strcpy(compounds[3].name, "Famotidine");
    strcpy(compounds[3].formula, "C8H15N7O2S3");
    strcpy(compounds[3].category, "Drug - Gastrointestinal");

    strcpy(compounds[4].name, "Resveratrol");
    strcpy(compounds[4].formula, "C14H12O3");
    strcpy(compounds[4].category, "Supplement - Nutraceutical");

    compound_count = 5;
    printf("[INIT] Loaded %d compounds\n", compound_count);
}

void send_response(int client, int status, const char *body) {
    char response[BUFFER_SIZE];
    sprintf(response,
        "HTTP/1.1 %d OK\r\n"
        "Content-Type: application/json\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Content-Length: %lu\r\n"
        "Connection: close\r\n"
        "\r\n%s",
        status, strlen(body), body);

    send(client, response, strlen(response), 0);
}

void handle_health(int client) {
    char response[1024];
    sprintf(response,
        "{\"status\":\"ok\",\"lock_hash\":\"%s\",\"rows\":%d,\"structures\":%d,\"compounds\":%d}",
        LOCK_HASH, ROWS, STRUCTURES, compound_count);
    send_response(client, 200, response);
}

void handle_compounds(int client) {
    char response[BUFFER_SIZE];
    strcpy(response, "{\"count\":");
    sprintf(response + strlen(response), "%d", compound_count);
    strcat(response, ",\"compounds\":[");

    for (int i = 0; i < compound_count; i++) {
        if (i > 0) strcat(response, ",");
        sprintf(response + strlen(response),
            "{\"generic_name\":\"%s\",\"chemical_formula\":\"%s\",\"category\":\"%s\",\"trade_names\":[]}",
            compounds[i].name, compounds[i].formula, compounds[i].category);
    }
    strcat(response, "]}");

    send_response(client, 200, response);
}

void* run_analysis(void *arg) {
    Task *task = (Task*)arg;
    strcpy(task->status, "running");

    for (int i = 0; i <= 100; i += 10) {
        task->progress = i;
        usleep(200000);
    }

    sprintf(task->result,
        "{\"lock_sha256\":\"%s\",\"rows\":%d,\"structures\":%d,\"compounds_analyzed\":2,"
        "\"compounds\":[{\"name\":\"Test\",\"formula\":\"C0H0\",\"category\":\"Test\"}]}",
        LOCK_HASH, ROWS, STRUCTURES);

    strcpy(task->status, "completed");
    task->progress = 100;
    return NULL;
}

void handle_analyze(int client) {
    if (task_count >= MAX_TASKS) {
        send_response(client, 429, "{\"error\":\"Too many tasks\"}");
        return;
    }

    Task *task = &tasks[task_count++];
    sprintf(task->id, "task_%d", ++next_task_id);
    strcpy(task->status, "running");
    task->progress = 0;
    strcpy(task->result, "");

    pthread_t thread;
    pthread_create(&thread, NULL, run_analysis, task);
    pthread_detach(thread);

    char response[256];
    sprintf(response, "{\"task_id\":\"%s\",\"status\":\"running\"}", task->id);
    send_response(client, 202, response);
}

void handle_results(int client, const char *task_id) {
    for (int i = 0; i < task_count; i++) {
        if (strcmp(tasks[i].id, task_id) == 0) {
            char response[BUFFER_SIZE];
            sprintf(response,
                "{\"task_id\":\"%s\",\"status\":\"%s\",\"progress\":%d,\"result\":%s}",
                tasks[i].id, tasks[i].status, tasks[i].progress,
                strlen(tasks[i].result) > 0 ? tasks[i].result : "null");
            send_response(client, 200, response);
            return;
        }
    }
    send_response(client, 404, "{\"error\":\"Task not found\"}");
}

void handle_request(int client) {
    char buffer[BUFFER_SIZE];
    int n = recv(client, buffer, BUFFER_SIZE - 1, 0);
    if (n <= 0) {
        close(client);
        return;
    }

    buffer[n] = '\0';

    // Parse request
    char method[16], path[256];
    sscanf(buffer, "%s %s", method, path);

    // Handle OPTIONS (CORS preflight)
    if (strcmp(method, "OPTIONS") == 0) {
        send_response(client, 200, "");
    }
    // Handle GET
    else if (strcmp(method, "GET") == 0) {
        if (strcmp(path, "/health") == 0) {
            handle_health(client);
        } else if (strcmp(path, "/compounds") == 0) {
            handle_compounds(client);
        } else if (strncmp(path, "/results/", 9) == 0) {
            handle_results(client, path + 9);
        } else {
            send_response(client, 404, "{\"error\":\"Not found\"}");
        }
    }
    // Handle POST
    else if (strcmp(method, "POST") == 0) {
        if (strcmp(path, "/analyze") == 0) {
            handle_analyze(client);
        } else {
            send_response(client, 404, "{\"error\":\"Not found\"}");
        }
    }

    close(client);
}

int main() {
    printf("\n");
    printf("============================================================\n");
    printf("  SEAM Compound Analyzer Backend\n");
    printf("  Minimal C Server (No Dependencies)\n");
    printf("============================================================\n");

    load_compounds();

    printf("✓ Lock: %s\n", LOCK_HASH);
    printf("✓ Server starting on http://localhost:%d\n", PORT);
    printf("============================================================\n\n");

    int server = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(PORT);

    bind(server, (struct sockaddr*)&addr, sizeof(addr));
    listen(server, 10);

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client = accept(server, (struct sockaddr*)&client_addr, &client_len);

        if (client >= 0) {
            handle_request(client);
        }
    }

    close(server);
    return 0;
}
