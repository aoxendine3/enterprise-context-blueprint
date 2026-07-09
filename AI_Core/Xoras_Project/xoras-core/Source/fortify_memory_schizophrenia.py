import asyncio
from xoras_memory_core import MemoryCore


async def fortify_memory():
    print("==========================================")
    print("      XORAS MEMORY FORTIFICATION          ")
    print("==========================================\n")

    # Initialize Memory Core
    memory = MemoryCore(
        db_path="/Users/ajoxendine68/Desktop/Xoras_Project/Source/xoras_memory.json")

    schizophrenia_pathology = """The pathophysiology of schizophrenia operates on three central axes:
1. Neurotransmitter imbalances: Subcortical hyperdopaminergia drives positive symptoms, while cortical hypodopaminergia and NMDA receptor hypofunction drive negative and cognitive symptoms.
2. Gut-Brain Axis and Leaky Gut: Dysbiosis leads to increased intestinal permeability, allowing inflammatory cytokines and neuroactive metabolites into systemic circulation, causing neuroinflammation.
3. Mitochondrial Complex I/IV dysfunction: Causes severe oxidative stress (ROS) and bioenergetic failure in the brain.
The target intervention is the Ketogenic Metabolic Recovery Pathway. It provides beta-hydroxybutyrate (BHB) as an alternative, highly efficient brain fuel, bypassing dysfunctional glucose transport (GLUT1). Ketones promote mitochondrial biogenesis, reduce ROS, and upregulate GAD67 to convert excitotoxic glutamate into inhibitory GABA, stabilizing neural networks."""

    print("\n[FORTIFICATION] Injecting Schizophrenia Pathology details into active memory...")
    await memory.memorize(schizophrenia_pathology, domain="biomedical_pathology")

    print("\n[VERIFICATION] Recalling memory regarding Schizophrenia / Ketogenic recovery...")
    result = await memory.recall("How does the ketogenic diet help with schizophrenia and mitochondria?", domain="biomedical_pathology")

    print(f"\n[RECALL RESULT]:\n{result}")
    print("\n==========================================")

if __name__ == "__main__":
    asyncio.run(fortify_memory())
