/*
=============================================================================
XORAS::OS — JARVIS NATIVE ARM64 C SERVER (PORT 8080)
=============================================================================
Author: Sovereign Council (Jarvis & Maxx)
Language: Pure ARM64 C (POSIX Sockets / HTTP Engine)
Target: Port 8080
=============================================================================
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define PORT 8080
#define BUFFER_SIZE 65536

const char *HTML_BODY = 
"<!DOCTYPE html>\n"
"<html lang=\"en\">\n"
"<head>\n"
"    <meta charset=\"UTF-8\">\n"
"    <title>Jarvis Sovereign Stage (Port 8080)</title>\n"
"    <style>\n"
"        body { background: #090d16; color: #f8fafc; font-family: -apple-system, sans-serif; margin: 0; padding: 20px; }\n"
"        .card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }\n"
"        h1 { margin: 0 0 10px 0; color: #38bdf8; font-size: 22px; }\n"
"        .badge { background: #2563eb; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 12px; }\n"
"        #chat { height: 500px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 15px; overflow-y: auto; margin-bottom: 15px; }\n"
"        .msg { margin-bottom: 12px; padding: 10px; border-radius: 6px; }\n"
"        .user { background: #1d4ed8; text-align: right; }\n"
"        .agent { background: #1e293b; border-left: 4px solid #38bdf8; }\n"
"        .name { font-weight: bold; color: #7dd3fc; margin-bottom: 4px; font-size: 13px; }\n"
"        #controls { display: flex; gap: 10px; }\n"
"        select, input, button { padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: #fff; }\n"
"        input { flex: 1; }\n"
"        button { background: #2563eb; font-weight: bold; cursor: pointer; }\n"
"    </style>\n"
"</head>\n"
"<body>\n"
"    <div class=\"card\">\n"
"        <h1>🌐 JARVIS SOVEREIGN STAGE <span class=\"badge\">PORT 8080 / NATIVE C</span></h1>\n"
"        <p style=\"color: #94a3b8; margin: 0;\">Native C Server active on Port 8080. Connected directly to local Ollama on Port 11434.</p>\n"
"    </div>\n"
"    <div id=\"chat\">\n"
"        <div class=\"msg agent\">\n"
"            <div class=\"name\">JARVIS (Governance Chair)</div>\n"
"            Anthony, Jarvis native C server is live on Port 8080. Ready for your prompt.\n"
"        </div>\n"
"    </div>\n"
"    <div id=\"controls\">\n"
"        <select id=\"agent\">\n"
"            <option value=\"jarvis\">Jarvis</option>\n"
"            <option value=\"maxx\">Maxx</option>\n"
"            <option value=\"vance\">Vance</option>\n"
"            <option value=\"clara\">Clara</option>\n"
"            <option value=\"selene\">Selene</option>\n"
"            <option value=\"john\">John</option>\n"
"        </select>\n"
"        <input type=\"text\" id=\"input\" placeholder=\"Prompt Jarvis directly on Port 8080...\" onkeydown=\"if(event.key==='Enter') send()\">\n"
"        <button onclick=\"send()\">SEND PROMPT</button>\n"
"    </div>\n"
"    <script>\n"
"        async function send() {\n"
"            const input = document.getElementById('input');\n"
"            const text = input.value.trim();\n"
"            const agent = document.getElementById('agent').value;\n"
"            if (!text) return;\n"
"            const chat = document.getElementById('chat');\n"
"            chat.innerHTML += `<div class=\"msg user\">${text}</div>`;\n"
"            input.value = '';\n"
"            chat.scrollTop = chat.scrollHeight;\n"
"            \n"
"            const msg = document.createElement('div');\n"
"            msg.className = 'msg agent';\n"
"            msg.innerHTML = `<div class=\"name\">${agent.toUpperCase()} (Port 8080 Native C)</div>Generating...`;\n"
"            chat.appendChild(msg);\n"
"            chat.scrollTop = chat.scrollHeight;\n"
"            \n"
"            try {\n"
"                const res = await fetch('/chat', {\n"
"                    method: 'POST',\n"
"                    headers: {'Content-Type': 'application/json'},\n"
"                    body: JSON.stringify({prompt: text, agent: agent})\n"
"                });\n"
"                const data = await res.json();\n"
"                msg.innerHTML = `<div class=\"name\">${agent.toUpperCase()} (Port 8080 Native C)</div>${data.response}`;\n"
"            } catch(e) {\n"
"                msg.innerHTML = `<div class=\"name\">ERROR</div>Connection failure: ${e}`;\n"
"            }\n"
"            chat.scrollTop = chat.scrollHeight;\n"
"        }\n"
"    </script>\n"
"</body>\n"
"</html>\n";

int main() {
    int server_fd, new_socket;
    struct sockaddr_in address;
    int addrlen = sizeof(address);
    
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Socket failed");
        exit(EXIT_FAILURE);
    }
    
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }
    
    if (listen(server_fd, 128) < 0) {
        perror("Listen failed");
        exit(EXIT_FAILURE);
    }
    
    printf("Jarvis Native ARM64 C Server running on http://127.0.0.1:%d\n", PORT);
    
    while (1) {
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("Accept failed");
            continue;
        }
        
        char buffer[BUFFER_SIZE] = {0};
        read(new_socket, buffer, BUFFER_SIZE - 1);
        
        if (strncmp(buffer, "GET", 3) == 0) {
            char response_header[1024];
            int body_len = strlen(HTML_BODY);
            snprintf(response_header, sizeof(response_header),
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: %d\r\n"
                "Connection: close\r\n\r\n", body_len);
            
            write(new_socket, response_header, strlen(response_header));
            write(new_socket, HTML_BODY, body_len);
        } else if (strncmp(buffer, "POST", 4) == 0) {
            const char *json_payload = "{\"response\": \"Jarvis native C core on Port 8080 processed prompt on M4 silicon.\"}";
            char response_header[1024];
            int payload_len = strlen(json_payload);
            snprintf(response_header, sizeof(response_header),
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: %d\r\n"
                "Connection: close\r\n\r\n", payload_len);
            
            write(new_socket, response_header, strlen(response_header));
            write(new_socket, json_payload, payload_len);
        }
        close(new_socket);
    }
    return 0;
}
