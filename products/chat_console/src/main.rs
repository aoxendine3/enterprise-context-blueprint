use axum::{routing::{get, post}, Router, Json};
use serde::{Deserialize, Serialize};
use tower_http::services::ServeDir;
use std::fs::{self, OpenOptions};
use std::io::{Write};
use std::env;

#[derive(Deserialize)]
struct ChatRequest { session_id: String, message: String }

#[derive(Serialize)]
struct ChatResponse { agent: String, reply: String }

#[derive(Serialize, Deserialize, Clone)]
struct Message { role: String, content: String }

#[tokio::main]
async fn main() {
    fs::create_dir_all("memory_store").unwrap();
    let app = Router::new()
        .route("/chat", post(chat_endpoint))
        .fallback_service(ServeDir::new("static"));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:8000").await.unwrap();
    println!("Sovereign Console live at http://127.0.0.1:8000");
    axum::serve(listener, app).await.unwrap();
}

async fn chat_endpoint(Json(req): Json<ChatRequest>) -> Json<ChatResponse> {
    let msg_lower = req.message.to_lowercase();
    let agent = if msg_lower.contains("code") || msg_lower.contains("bug") || msg_lower.contains("rust") || msg_lower.contains("zig") {
        "Coder"
    } else if msg_lower.contains("research") || msg_lower.contains("who") || msg_lower.contains("explain") {
        "Researcher"
    } else {
        "General"
    };

    append_memory(&req.session_id, agent, "user", &req.message);
    let history = get_memory(&req.session_id, agent, 20);
    
    let reply = match call_openai(agent, history).await {
        Ok(r) => r,
        Err(e) => {
            println!("[API ERROR] {}", e);
            format!("[{} SYSTEM FAULT]: {}", agent, e)
        }
    };
    
    append_memory(&req.session_id, agent, "assistant", &reply);

    Json(ChatResponse { agent: agent.to_string(), reply })
}

fn append_memory(session: &str, agent: &str, role: &str, content: &str) {
    let path = format!("memory_store/{}_{}.jsonl", session, agent);
    let mut file = OpenOptions::new().create(true).append(true).open(path).unwrap();
    let msg = Message { role: role.to_string(), content: content.to_string() };
    let json = serde_json::to_string(&msg).unwrap();
    writeln!(file, "{}", json).unwrap();
}

fn get_memory(session: &str, agent: &str, limit: usize) -> Vec<Message> {
    let path = format!("memory_store/{}_{}.jsonl", session, agent);
    let mut msgs = Vec::new();
    if let Ok(content) = fs::read_to_string(path) {
        for line in content.lines() {
            if let Ok(msg) = serde_json::from_str::<Message>(line) {
                msgs.push(msg);
            }
        }
    }
    if msgs.len() > limit { msgs.split_off(msgs.len() - limit) } else { msgs }
}

async fn call_openai(agent: &str, history: Vec<Message>) -> Result<String, String> {
    let api_key = env::var("OPENAI_API_KEY").unwrap_or_default();
    if api_key.is_empty() {
        return Err("OPENAI_API_KEY environment variable is missing.".to_string());
    }

    let prompt = match agent {
        "Coder" => "You are an elite software engineer. Write working code. No fluff.",
        "Researcher" => "You are a deep-dive researcher. Provide factual answers.",
        _ => "You are a sharp general assistant.",
    };

    let mut messages = vec![serde_json::json!({"role": "system", "content": prompt})];
    for msg in history { messages.push(serde_json::json!({"role": msg.role, "content": msg.content})); }

    let client = reqwest::Client::new();
    let res = match client.post("https://api.openai.com/v1/chat/completions")
        .bearer_auth(api_key)
        .json(&serde_json::json!({
            "model": "gpt-4o-mini",
            "messages": messages
        }))
        .send()
        .await {
            Ok(response) => response,
            Err(e) => return Err(format!("Network Failure: {}", e))
        };

    if !res.status().is_success() {
        let status = res.status();
        let body = res.text().await.unwrap_or_default();
        return Err(format!("OpenAI Rejection ({}): {}", status, body));
    }

    let json: serde_json::Value = match res.json().await {
        Ok(j) => j,
        Err(e) => return Err(format!("JSON Parse Failure: {}", e))
    };

    if let Some(content) = json["choices"][0]["message"]["content"].as_str() {
        Ok(content.to_string())
    } else {
        Err("API Payload lacked choices[0].message.content".to_string())
    }
}
