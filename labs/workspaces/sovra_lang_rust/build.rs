// build.rs
fn main() {
    // Compile the original C source into an object file
    cc::Build::new()
        .file("../sovra_lang/context_bridge_engine.c")
        .include("../sovra_lang")
        .compile("context_bridge_engine");
    // Ensure linker can find the static library (the compiled object will be linked automatically)
    println!("cargo:rustc-link-lib=static=context_bridge_engine");
    // On macOS we might need to link with the system libraries for pthread etc.
    println!("cargo:rustc-link-lib=framework=CoreFoundation");
    println!("cargo:rustc-link-lib=pthread");
}
