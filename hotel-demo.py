import streamlit as st
import subprocess
import sys
import os
from datetime import datetime
import time
import threading
import queue
import warnings

# Configure for presentation mode
st.set_page_config(
    page_title="Hotel AI Agents - Live Demo",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Windows Encoding Setup ---
def setup_console_encoding():
    """Setup console for Unicode support on Windows."""
    if sys.platform == "win32":
        try:
            # Try to set UTF-8 encoding for Windows console
            os.system("chcp 65001 > nul 2>&1")
            return True
        except:
            return False
    return True

# --- Safe Text Processing ---
def safe_text_processing(text):
    """Safely process text to handle encoding issues."""
    if not text:
        return ""
    
    try:
        # Ensure text is properly encoded
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        
        # Replace problematic Unicode characters with safe alternatives
        emoji_replacements = {
            '🏨': '[HOTEL]',
            '🎫': '[CHECKIN]', 
            '🎧': '[SERVICE]',
            '🍽️': '[F&B]',
            '💰': '[FINANCE]',
            '👥': '[HR]',
            '🔧': '[MAINTENANCE]',
            '🎯': '[MARKETING]',
            '🚀': '[START]',
            '⏰': '[TIMEOUT]',
            '❌': '[ERROR]',
            '✅': '[SUCCESS]',
            '📊': '[DATA]',
            '🤖': '[AI]',
            '📄': '[FILE]'
        }
        
        for emoji, replacement in emoji_replacements.items():
            text = text.replace(emoji, replacement)
            
        return text
    except Exception as e:
        return f"[TEXT PROCESSING ERROR: {str(e)}]"

# Custom CSS for presentation
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 2rem;
        font-weight: bold;
    }
    .agent-selector {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 2px solid #e2e8f0;
    }
    .demo-controls {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
    .status-bar {
        background: #f1f5f9;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #3b82f6;
        margin-top: 1rem;
    }
    .agent-info {
        background: #eff6ff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dbeafe;
        margin: 1rem 0;
    }
    .error-message {
        background: #fef2f2;
        color: #dc2626;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #fecaca;
        margin: 1rem 0;
    }
    .success-message {
        background: #f0fdf4;
        color: #16a34a;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #bbf7d0;
        margin: 1rem 0;
    }
    .output-header {
        background: #374151;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px 8px 0 0;
        font-weight: bold;
        margin-bottom: 0;
    }
    .stCodeBlock {
        margin-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

class AgentDemo:
    def __init__(self):
        # Setup encoding
        setup_console_encoding()
        
        self.agents = {
            "Check-in Processor": {
                "file": "checkin-agent.py",
                "description": "Processes guest arrivals and personalised check-ins",
                "icon": "[CHECKIN]",
                "demo_data": "Sample booking data: Alice Wonderland, Room 305, VIP guest",
                "expected_output": "Guest processing and room assignment"
            },
            "Customer Service": {
                "file": "customerservice-agent.py", 
                "description": "Intelligent FAQ resolution and escalation management",
                "icon": "[SERVICE]",
                "demo_data": "Guest inquiry: 'What time is breakfast served?'",
                "expected_output": "FAQ analysis and knowledge base management"
            },
            "F&B Management": {
                "file": "fb-agent.py",
                "description": "Inventory optimisation and menu engineering",
                "icon": "[F&B]",
                "demo_data": "Analysing 25 inventory items across 5 categories",
                "expected_output": "Inventory analysis and menu optimization"
            },
            "Finance Processor": {
                "file": "finance-agent.py",
                "description": "Automated invoice verification and matching",
                "icon": "[FINANCE]",
                "demo_data": "Processing 7 invoices against purchase orders",
                "expected_output": "Invoice verification and discrepancy detection"
            },
            "HR Assistant": {
                "file": "hr-agent.py",
                "description": "Employee onboarding and progress tracking",
                "icon": "[HR]",
                "demo_data": "Managing 6 new hires across different departments",
                "expected_output": "Onboarding progress analysis"
            },
            "Maintenance Coordinator": {
                "file": "maintenance-agent3.py",
                "description": "Predictive maintenance and property care",
                "icon": "[MAINTENANCE]",
                "demo_data": "Monitoring 25 assets with IoT integration",
                "expected_output": "Asset health analysis and maintenance recommendations"
            },
            "Marketing Engine": {
                "file": "marketing-agent.py",
                "description": "Personalised guest marketing and offers",
                "icon": "[MARKETING]",
                "demo_data": "Creating targeted offers for 8 guest profiles",
                "expected_output": "Personalised marketing offers generation"
            }
        }
        
        # Initialize session state
        if 'agent_output' not in st.session_state:
            st.session_state.agent_output = ""
        if 'agent_running' not in st.session_state:
            st.session_state.agent_running = False
        if 'last_agent' not in st.session_state:
            st.session_state.last_agent = None

    def validate_agent_file(self, agent_file):
        """Validate that the agent file exists and is accessible."""
        if not os.path.exists(agent_file):
            return False, f"Agent file '{agent_file}' not found"
        
        if not agent_file.endswith('.py'):
            return False, f"File '{agent_file}' is not a Python script"
            
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read(100)  # Read first 100 chars to verify
            return True, "File is accessible"
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"

    def run_agent_with_encoding(self, agent_file):
        """Run the selected agent with comprehensive encoding handling."""
        try:
            # Validate file first
            is_valid, message = self.validate_agent_file(agent_file)
            if not is_valid:
                return f"[ERROR] {message}"
            
            # Set comprehensive environment for UTF-8
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONHASHSEED'] = '0'
            
            # Windows-specific encoding setup
            if sys.platform == "win32":
                env['CHCP'] = '65001'  # UTF-8 code page
            
            # Add current directory to Python path
            current_dir = os.getcwd()
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{current_dir};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = current_dir
            
            # Run the agent with comprehensive error handling
            st.session_state.agent_output += f"[START] Executing {agent_file}...\n"
            st.session_state.agent_output += f"[INFO] Environment: Python {sys.version.split()[0]}\n"
            st.session_state.agent_output += f"[INFO] Platform: {sys.platform}\n"
            st.session_state.agent_output += f"[INFO] Working Directory: {current_dir}\n"
            st.session_state.agent_output += "-" * 60 + "\n"
            
            # Use Popen for better real-time output
            process = subprocess.Popen(
                [sys.executable, agent_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output in real-time
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Process and clean the output
                    clean_output = safe_text_processing(output.strip())
                    output_lines.append(clean_output)
                    
                    # Update session state for real-time display
                    st.session_state.agent_output += clean_output + "\n"
                    
                    # Limit output length to prevent memory issues
                    if len(st.session_state.agent_output) > 15000:
                        lines = st.session_state.agent_output.split('\n')
                        st.session_state.agent_output = '\n'.join(lines[-100:])  # Keep last 100 lines
            
            # Wait for process to complete
            return_code = process.wait()
            
            # Add completion status
            if return_code == 0:
                completion_msg = f"\n[SUCCESS] Agent completed successfully (exit code: {return_code})"
            else:
                completion_msg = f"\n[WARNING] Agent completed with exit code: {return_code}"
            
            st.session_state.agent_output += completion_msg + "\n"
            
            return "\n".join(output_lines) + completion_msg
            
        except subprocess.TimeoutExpired:
            error_msg = "[TIMEOUT] Agent processing timeout - Demo completed after 2 minutes"
            st.session_state.agent_output += error_msg + "\n"
            return error_msg
        except FileNotFoundError:
            error_msg = f"[ERROR] Python interpreter or agent file not found"
            st.session_state.agent_output += error_msg + "\n"
            return error_msg
        except Exception as e:
            error_msg = f"[ERROR] Unexpected error: {str(e)}"
            st.session_state.agent_output += error_msg + "\n"
            return error_msg

    def display_demo_interface(self):
        """Display the main demo interface."""
        
        # Header
        st.markdown("""
        <div class="main-header">
            [HOTEL] The Grand Serenity Hotel - Live AI Agent Demo
        </div>
        """, unsafe_allow_html=True)

        # Create two columns for layout
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("""
            <div class="agent-selector">
                <h3>[AI] Select AI Agent</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Agent selection
            selected_agent = st.selectbox(
                "Choose an agent to demonstrate:",
                list(self.agents.keys()),
                format_func=lambda x: f"{self.agents[x]['icon']} {x}"
            )
            
            if selected_agent:
                agent_info = self.agents[selected_agent]
                
                # Display agent information
                st.markdown(f"""
                <div class="agent-info">
                    <h4>{agent_info['icon']} {selected_agent}</h4>
                    <p><strong>Description:</strong> {agent_info['description']}</p>
                    <p><strong>Demo Scenario:</strong> {agent_info['demo_data']}</p>
                    <p><strong>Expected Output:</strong> {agent_info['expected_output']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # File validation
                is_valid, validation_msg = self.validate_agent_file(agent_info['file'])
                if not is_valid:
                    st.markdown(f"""
                    <div class="error-message">
                        <strong>[ERROR] File Validation Failed:</strong> {validation_msg}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="success-message">
                        <strong>[SUCCESS] Agent Ready:</strong> {agent_info['file']} is accessible
                    </div>
                    """, unsafe_allow_html=True)
                
                # Demo controls
                col_start, col_stop = st.columns(2)
                
                with col_start:
                    start_disabled = st.session_state.agent_running or not is_valid
                    if st.button(
                        f"▶️ Start {selected_agent}", 
                        disabled=start_disabled,
                        help="Click to start the AI agent demo"
                    ):
                        st.session_state.agent_running = True
                        st.session_state.last_agent = selected_agent
                        st.session_state.agent_output = f"[START] Initialising {selected_agent}...\n"
                        
                        # Create a placeholder for real-time updates
                        with st.spinner(f"[AI] {selected_agent} is processing..."):
                            # Run agent with encoding handling
                            output = self.run_agent_with_encoding(agent_info['file'])
                            st.session_state.agent_running = False
                        
                        st.rerun()
                
                with col_stop:
                    if st.button(
                        "⏹️ Clear Output", 
                        help="Clear the output window"
                    ):
                        st.session_state.agent_output = ""
                        st.session_state.agent_running = False
                        st.session_state.last_agent = None
                        st.rerun()

        with col2:
            st.markdown("""
            <div class="agent-selector">
                <h3>[DATA] Live Agent Output</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Output display using st.code() for terminal-like appearance
            output_content = st.session_state.agent_output if st.session_state.agent_output else "No output yet. Select an agent and click Start to begin."
            
            # Add a header for the terminal window
            st.markdown('<div class="output-header">🖥️ Agent Terminal Output</div>', unsafe_allow_html=True)
            
            # Use st.code for clean, terminal-like display
            st.code(
                output_content,
                language=None,  # Plain text, no syntax highlighting
                line_numbers=False,
                wrap_lines=True
            )
            
            # Control buttons and download
            col_download, col_scroll = st.columns(2)
            
            with col_download:
                if st.session_state.agent_output:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"agent_demo_output_{timestamp}.txt"
                    
                    st.download_button(
                        label="💾 Download Output",
                        data=st.session_state.agent_output,
                        file_name=filename,
                        mime="text/plain",
                        help="Download the complete agent output as a text file"
                    )
            
            with col_scroll:
                if st.button("🔄 Auto-scroll to Bottom", help="Scroll to the latest output"):
                    st.rerun()

        # Enhanced status bar
        if st.session_state.agent_running:
            status_color = "#dc2626"  # Red
            status_text = f"[RUNNING] Agent Processing: {st.session_state.last_agent or 'Unknown'}"
            status_icon = "🔴"
        else:
            status_color = "#16a34a"  # Green
            status_text = "[READY] Select an agent and click Start to begin demo"
            status_icon = "🟢"
        
        st.markdown(f"""
        <div class="status-bar" style="border-left-color: {status_color};">
            <strong>Status:</strong> {status_icon} {status_text} | 
            <strong>Time:</strong> {datetime.now().strftime('%H:%M:%S')} | 
            <strong>Platform:</strong> {sys.platform} | 
            <strong>Encoding:</strong> UTF-8
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-refresh for live updates (reduced frequency)
        if st.session_state.agent_running:
            time.sleep(1)
            st.rerun()

def main():
    """Main application entry point."""
    try:
        # Setup encoding for the application
        if not setup_console_encoding():
            st.warning("⚠️ Could not setup UTF-8 encoding. Some characters may not display correctly.")
        
        # Suppress warnings
        warnings.filterwarnings("ignore")
        
        demo = AgentDemo()
        demo.display_demo_interface()
        
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.info("Try refreshing the page or checking the console for more details.")

if __name__ == "__main__":
    main()
