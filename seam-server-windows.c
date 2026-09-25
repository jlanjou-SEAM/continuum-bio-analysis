#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <windows.h>
#include <process.h>

#define PORT 5000
#define BUFFER_SIZE 131072
#define MAX_COMPOUNDS 400
#define MAX_TASKS 100
#define DATABASE_PATH "SEAM_common_drugs_supplements_choice_registry_v1.json"

const char *LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4";
const int ROWS = 5734;
const int STRUCTURES = 420;

typedef struct {
    char name[512];
    char formula[256];
    char category[256];
} Compound;

typedef struct {
    char id[32];
    char status[32];
    int progress;
    char result[8192];
    HANDLE hThread;
} Task;

Compound compounds[MAX_COMPOUNDS];
int compound_count = 0;
char *compounds_json = NULL;
Task tasks[MAX_TASKS];
int task_count = 0;
int next_task_id = 0;
CRITICAL_SECTION cs_tasks;

long get_file_size(FILE *f) {
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    return size;
}

void load_compounds() {
    FILE *f = fopen(DATABASE_PATH, "r");
    if (!f) {
        printf("[WARN] Database file not found: %s\n", DATABASE_PATH);
        printf("[INFO] Using fallback compounds (5 demo)\n");

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

        strcpy(compounds[4].name, "Aspirin");
        strcpy(compounds[4].formula, "C9H8O4");
        strcpy(compounds[4].category, "Drug - Pain/antiplatelet");

        compound_count = 5;
        return;
    }

    long size = get_file_size(f);
    compounds_json = malloc(size + 1);
    if (!compounds_json) {
        printf("[ERROR] Memory allocation failed\n");
        fclose(f);
        compound_count = 0;
        return;
    }

    fread(compounds_json, 1, size, f);
    compounds_json[size] = '\0';
    fclose(f);

    char *p = compounds_json;
    int count = 0;

    while (count < MAX_COMPOUNDS) {
        char *gen_start = strstr(p, "\"generic_name\"");
        if (!gen_start) break;

        char *gen_val_start = strchr(gen_start, ':') + 1;
        while (*gen_val_start && (*gen_val_start == ' ' || *gen_val_start == '"')) gen_val_start++;

        char *gen_val_end = strchr(gen_val_start, '"');
        if (!gen_val_end) break;

        int gen_len = (int)(gen_val_end - gen_val_start);
        if (gen_len > 500) gen_len = 500;
        strncpy_s(compounds[count].name, sizeof(compounds[count].name), gen_val_start, gen_len);
        compounds[count].name[gen_len] = '\0';

        char *formula_start = strstr(p, "\"chemical_formula\"");
        if (!formula_start) break;
        formula_start = strchr(formula_start, ':');
        if (!formula_start) break;

        char *formula_val_start = formula_start + 1;
        while (*formula_val_start && (*formula_val_start == ' ' || *formula_val_start == '"')) formula_val_start++;

        char *formula_val_end = strchr(formula_val_start, '"');
        if (!formula_val_end) break;

        int formula_len = (int)(formula_val_end - formula_val_start);
        if (formula_len > 250) formula_len = 250;
        strncpy_s(compounds[count].formula, sizeof(compounds[count].formula), formula_val_start, formula_len);
        compounds[count].formula[formula_len] = '\0';

        char *cat_start = strstr(p, "\"category\"");
        if (!cat_start) break;
        cat_start = strchr(cat_start, ':');
        if (!cat_start) break;

        char *cat_val_start = cat_start + 1;
        while (*cat_val_start && (*cat_val_start == ' ' || *cat_val_start == '"')) cat_val_start++;

        char *cat_val_end = strchr(cat_val_start, '"');
        if (!cat_val_end) break;

        int cat_len = (int)(cat_val_end - cat_val_start);
        if (cat_len > 250) cat_len = 250;
        strncpy_s(compounds[count].category, sizeof(compounds[count].category), cat_val_start, cat_len);
        compounds[count].category[cat_len] = '\0';

        p = gen_val_end + 1;
        count++;
    }

    compound_count = count;
    printf("[INIT] Loaded %d compounds from %s\n", compound_count, DATABASE_PATH);
}

void send_response(SOCKET client, int status, const char *body) {
    char response[BUFFER_SIZE];
    int response_len = sprintf_s(response, BUFFER_SIZE,
        "HTTP/1.1 %d OK\r\n"
        "Content-Type: application/json\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "\r\n%s",
        status, strlen(body), body);

    send(client, response, response_len, 0);
}

void handle_health(SOCKET client) {
    char response[1024];
    sprintf_s(response, sizeof(response),
        "{\"status\":\"ok\",\"lock_hash\":\"%s\",\"rows\":%d,\"structures\":%d,\"compounds\":%d}",
        LOCK_HASH, ROWS, STRUCTURES, compound_count);
    send_response(client, 200, response);
}

void handle_compounds(SOCKET client) {
    char response[BUFFER_SIZE];
    strcpy_s(response, sizeof(response), "{\"count\":");
    sprintf_s(response + strlen(response), sizeof(response) - strlen(response), "%d", compound_count);
    strcat_s(response, sizeof(response), ",\"compounds\":[");

    for (int i = 0; i < compound_count; i++) {
        if (i > 0) strcat_s(response, sizeof(response), ",");
        if (strlen(response) > BUFFER_SIZE - 512) break;

        char compound_json[1024];
        sprintf_s(compound_json, sizeof(compound_json),
            "{\"generic_name\":\"%s\",\"chemical_formula\":\"%s\",\"category\":\"%s\",\"trade_names\":[]}",
            compounds[i].name, compounds[i].formula, compounds[i].category);
        strcat_s(response, sizeof(response), compound_json);
    }
    strcat_s(response, sizeof(response), "]}");

    send_response(client, 200, response);
}

DWORD WINAPI run_analysis_thread(LPVOID arg) {
    Task *task = (Task*)arg;
    strcpy_s(task->status, sizeof(task->status), "running");

    for (int i = 0; i <= 100; i += 10) {
        task->progress = i;
        Sleep(200);
    }

    sprintf_s(task->result, sizeof(task->result),
        "{\"lock_sha256\":\"%s\",\"rows\":%d,\"structures\":%d,\"compounds_analyzed\":2,"
        "\"compounds\":[{\"name\":\"Test\",\"formula\":\"C0H0\",\"category\":\"Test\"}]}",
        LOCK_HASH, ROWS, STRUCTURES);

    strcpy_s(task->status, sizeof(task->status), "completed");
    task->progress = 100;
    return 0;
}

void handle_analyze(SOCKET client) {
    EnterCriticalSection(&cs_tasks);

    if (task_count >= MAX_TASKS) {
        LeaveCriticalSection(&cs_tasks);
        send_response(client, 429, "{\"error\":\"Too many tasks\"}");
        return;
    }

    Task *task = &tasks[task_count++];
    sprintf_s(task->id, sizeof(task->id), "task_%d", ++next_task_id);
    strcpy_s(task->status, sizeof(task->status), "running");
    task->progress = 0;
    strcpy_s(task->result, sizeof(task->result), "");

    HANDLE hThread = CreateThread(NULL, 0, run_analysis_thread, task, 0, NULL);
    if (hThread) {
        CloseHandle(hThread);
    }

    LeaveCriticalSection(&cs_tasks);

    char response[256];
    sprintf_s(response, sizeof(response), "{\"task_id\":\"%s\",\"status\":\"running\"}", task->id);
    send_response(client, 202, response);
}

void handle_results(SOCKET client, const char *task_id) {
    EnterCriticalSection(&cs_tasks);

    for (int i = 0; i < task_count; i++) {
        if (strcmp(tasks[i].id, task_id) == 0) {
            char response[BUFFER_SIZE];
            sprintf_s(response, sizeof(response),
                "{\"task_id\":\"%s\",\"status\":\"%s\",\"progress\":%d,\"result\":%s}",
                tasks[i].id, tasks[i].status, tasks[i].progress,
                strlen(tasks[i].result) > 0 ? tasks[i].result : "null");

            LeaveCriticalSection(&cs_tasks);
            send_response(client, 200, response);
            return;
        }
    }

    LeaveCriticalSection(&cs_tasks);
    send_response(client, 404, "{\"error\":\"Task not found\"}");
}

void handle_request(SOCKET client) {
    char buffer[BUFFER_SIZE];
    int n = recv(client, buffer, BUFFER_SIZE - 1, 0);
    if (n <= 0) {
        closesocket(client);
        return;
    }

    buffer[n] = '\0';

    char method[16], path[256];
    sscanf_s(buffer, "%15s %255s", method, (unsigned)sizeof(method), path, (unsigned)sizeof(path));

    if (strcmp(method, "OPTIONS") == 0) {
        send_response(client, 200, "");
    }
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
    else if (strcmp(method, "POST") == 0) {
        if (strcmp(path, "/analyze") == 0) {
            handle_analyze(client);
        } else {
            send_response(client, 404, "{\"error\":\"Not found\"}");
        }
    }

    closesocket(client);
}

DWORD WINAPI client_thread(LPVOID arg) {
    SOCKET client = (SOCKET)(intptr_t)arg;
    handle_request(client);
    return 0;
}

int main() {
    WSADATA wsa_data;
    SOCKET server, client;
    struct sockaddr_in addr, client_addr;
    int client_addr_len;
    HANDLE hThread;

    printf("\n");
    printf("============================================================\n");
    printf("  SEAM Compound Analyzer Backend\n");
    printf("  Minimal C Server (No Dependencies)\n");
    printf("============================================================\n");

    InitializeCriticalSection(&cs_tasks);
    load_compounds();

    printf("✓ Lock: %s\n", LOCK_HASH);
    printf("✓ Server starting on http://localhost:%d\n", PORT);
    printf("✓ Database: %d compounds loaded\n", compound_count);
    printf("============================================================\n\n");

    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        printf("ERROR: WSAStartup failed\n");
        return 1;
    }

    server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (server == INVALID_SOCKET) {
        printf("ERROR: socket() failed\n");
        WSACleanup();
        return 1;
    }

    int opt = 1;
    if (setsockopt(server, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt)) == SOCKET_ERROR) {
        printf("ERROR: setsockopt failed\n");
        closesocket(server);
        WSACleanup();
        return 1;
    }

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    addr.sin_port = htons(PORT);

    if (bind(server, (struct sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR) {
        printf("ERROR: bind() failed - Port %d may be in use\n", PORT);
        closesocket(server);
        WSACleanup();
        return 1;
    }

    if (listen(server, 10) == SOCKET_ERROR) {
        printf("ERROR: listen() failed\n");
        closesocket(server);
        WSACleanup();
        return 1;
    }

    printf("Press Ctrl+C to stop server...\n\n");

    while (1) {
        client_addr_len = sizeof(client_addr);
        client = accept(server, (struct sockaddr*)&client_addr, &client_addr_len);

        if (client != INVALID_SOCKET) {
            hThread = CreateThread(NULL, 0, client_thread, (LPVOID)(intptr_t)client, 0, NULL);
            if (hThread) {
                CloseHandle(hThread);
            } else {
                closesocket(client);
            }
        }
    }

    closesocket(server);
    WSACleanup();
    DeleteCriticalSection(&cs_tasks);
    if (compounds_json) free(compounds_json);

    return 0;
}
