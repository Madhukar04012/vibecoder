"""
Team Lead Agent - The AI Project Manager
Handles conversation, requirements gathering, and plan creation with safe fallbacks.
"""

from typing import List
import json
from sqlalchemy.orm import Session
from backend.models.project import Project
from backend.models.project_agent import ProjectAgent
from backend.models.conversation import Conversation
from backend.models.project_plan import ProjectPlan
from backend.core.llm_client import call_llm  # call_ollama is an alias in llm_client for backward compat
from backend.schemas.team_lead import TeamLeadResponse, PlanOutput, TechStack, ClarificationQuestion


class TeamLeadAgent:
    def __init__(self, project_id: str, db: Session):
        self.project_id = project_id
        self.db = db
        self.agent_role = "team_lead"
        self._ensure_agent_exists()

    def _ensure_agent_exists(self):
        """Ensure the agent record exists in DB"""
        agent = self.db.query(ProjectAgent).filter(
            ProjectAgent.project_id == self.project_id,
            ProjectAgent.role == self.agent_role
        ).first()
        
        if not agent:
            # Initialize new agent
            agent = ProjectAgent(
                project_id=self.project_id,
                role=self.agent_role,
                state_json=json.dumps({"phase": "discovery"})
            )
            self.db.add(agent)
            self.db.commit()

    def _save_message(self, role: str, message: str):
        """Save message to conversation history"""
        msg = Conversation(
            project_id=self.project_id,
            role=role,
            message=message
        )
        self.db.add(msg)
        self.db.commit()
        return msg

    # ---------- SAFE CORE (FALLBACKS) ----------

    def _needs_clarification(self, idea: str) -> bool:
        """Check if idea is too vague"""
        return len(idea.split()) < 5

    def _ask_questions_fallback(self) -> List[ClarificationQuestion]:
        """Deterministic questions for vague ideas"""
        return [
            ClarificationQuestion(id=1, question="Is this a web app or mobile app?"),
            ClarificationQuestion(id=2, question="Will users need to sign up and log in?"),
            ClarificationQuestion(id=3, question="What is the key feature users will pay for?")
        ]

    def _generate_plan_fallback(self, idea: str) -> PlanOutput:
        """Deterministic plan if AI fails"""
        return PlanOutput(
            summary=f"Professional web application for: {idea}",
            tech_stack=TechStack(
                backend="FastAPI",
                frontend="React",
                database="PostgreSQL"
            ),
            modules=["Authentication", "Dashboard", "Settings"],
            features=["User Login", "Responsive UI", "API Integration"],
            assumptions=["Web-based platform", "Standard email auth"]
        )

    # ---------- AI LOGIC ----------

    def process_input(self, user_input: str) -> TeamLeadResponse:
        """
        Main logic flow:
        1. Save user input
        2. Decide (Question vs Plan)
        3. Fallback handle
        """
        # 1. Save user message
        self._save_message("user", user_input)
        
        # 2. Check if we need simple clarification first (deterministic check)
        if self._needs_clarification(user_input):
            questions = self._ask_questions_fallback()
            # Save AI response text representation
            self._save_message("team_lead", "I need a few clarifications to proceed.")
            return TeamLeadResponse(type="questions", questions=questions)

        # 3. Try AI Planning
        try:
            plan = self._generate_plan_ai(user_input)
            # Save AI response
            self._save_message("team_lead", f"I've created a plan for '{user_input}'. Please review.")
            return TeamLeadResponse(type="plan", plan=plan)
        
        except Exception as e:
            print(f"[TeamLead] AI failed: {e}. Using fallback.")
            # 4. Fallback Plan
            plan = self._generate_plan_fallback(user_input)
            self._save_message("team_lead", "I've created a draft plan based on best practices.")
            return TeamLeadResponse(type="plan", plan=plan)

    def _generate_plan_ai(self, idea: str) -> PlanOutput:
        """Call LLM to generate plan JSON"""
        project = self.db.query(Project).filter(Project.id == self.project_id).first()
        
        prompt = f"""Create a detailed technical architecture JSON for this project.
Project Idea: {idea}

Output ONLY valid JSON in this exact structure:
{{
  "summary": "High level summary",
  "tech_stack": {{ "backend": "tech", "frontend": "tech", "database": "tech" }},
  "modules": ["list", "of", "modules"],
  "features": ["list", "of", "features"],
  "assumptions": ["list of assumptions"]
}}
"""
        response = call_llm(prompt)
        
        if not response:
            raise ValueError("Empty AI response")
            
        return PlanOutput(**response)

    def save_plan(self, plan: PlanOutput):
        """Save plan to database"""
        # Update/Create ProjectPlan
        project_plan = self.db.query(ProjectPlan).filter(
            ProjectPlan.project_id == self.project_id
        ).first()
        
        if not project_plan:
            project_plan = ProjectPlan(
                project_id=self.project_id,
                architecture_json=plan.model_dump_json(),
                approved=False
            )
            self.db.add(project_plan)
        else:
            project_plan.architecture_json = plan.model_dump_json()
        
        self.db.commit()
        return project_plan
