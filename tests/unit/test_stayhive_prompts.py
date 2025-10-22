"""Unit tests for StayHive MCP prompts"""
import pytest
from mcp_servers.stayhive import prompts


@pytest.mark.unit
class TestGuestGreetingPrompt:
    """Test the guest greeting prompt templates"""

    @pytest.mark.asyncio
    async def test_guest_greeting_friendly_style(self):
        """Test friendly greeting style"""
        result = await prompts.guest_greeting_prompt(style="friendly")

        assert isinstance(result, dict)
        assert "name" in result
        assert "template" in result
        assert "example" in result
        assert "Friendly" in result["name"]
        assert len(result["template"]) > 50
        assert "warm" in result["template"].lower() or "friendly" in result["template"].lower()

    @pytest.mark.asyncio
    async def test_guest_greeting_formal_style(self):
        """Test formal greeting style"""
        result = await prompts.guest_greeting_prompt(style="formal")

        assert isinstance(result, dict)
        assert "Professional" in result["name"] or "Formal" in result["name"]
        assert "professional" in result["template"].lower() or "formal" in result["template"].lower()

    @pytest.mark.asyncio
    async def test_guest_greeting_casual_style(self):
        """Test casual greeting style"""
        result = await prompts.guest_greeting_prompt(style="casual")

        assert isinstance(result, dict)
        assert "Casual" in result["name"]
        assert "casual" in result["template"].lower() or "relaxed" in result["template"].lower()

    @pytest.mark.asyncio
    async def test_guest_greeting_default_style(self):
        """Test default greeting style (should be friendly)"""
        result = await prompts.guest_greeting_prompt()

        assert isinstance(result, dict)
        assert "template" in result
        # Default should be friendly
        assert len(result["template"]) > 0

    @pytest.mark.asyncio
    async def test_guest_greeting_has_example(self):
        """Test that all greeting styles include examples"""
        styles = ["friendly", "formal", "casual"]

        for style in styles:
            result = await prompts.guest_greeting_prompt(style=style)
            assert "example" in result
            assert len(result["example"]) > 0
            assert "West Bethel Motel" in result["example"] or "welcome" in result["example"].lower()


@pytest.mark.unit
class TestAvailabilityInquiryPrompt:
    """Test the availability inquiry prompt template"""

    @pytest.mark.asyncio
    async def test_availability_inquiry_structure(self):
        """Test availability inquiry prompt structure"""
        result = await prompts.availability_inquiry_prompt()

        assert isinstance(result, dict)
        assert "name" in result
        assert "template" in result
        assert "Availability" in result["name"]

    @pytest.mark.asyncio
    async def test_availability_inquiry_required_info(self):
        """Test that prompt mentions required information"""
        result = await prompts.availability_inquiry_prompt()

        template = result["template"]
        # Should mention what information is needed
        assert "check-in" in template.lower() or "check in" in template.lower()
        assert "check-out" in template.lower() or "check out" in template.lower()
        assert "adults" in template.lower() or "guests" in template.lower()

    @pytest.mark.asyncio
    async def test_availability_inquiry_mentions_tool(self):
        """Test that prompt references the availability tool"""
        result = await prompts.availability_inquiry_prompt()

        template = result["template"]
        assert "check_availability" in template or "tool" in template.lower()

    @pytest.mark.asyncio
    async def test_availability_inquiry_has_example_flow(self):
        """Test that prompt includes example conversation flow"""
        result = await prompts.availability_inquiry_prompt()

        # Should have either example or example_flow
        has_example = "example" in result or "example_flow" in result
        assert has_example


@pytest.mark.unit
class TestBookingConfirmationPrompt:
    """Test the booking confirmation prompt template"""

    @pytest.mark.asyncio
    async def test_booking_confirmation_structure(self):
        """Test booking confirmation prompt structure"""
        result = await prompts.booking_confirmation_prompt()

        assert isinstance(result, dict)
        assert "name" in result
        assert "template" in result
        assert "Booking" in result["name"] or "Confirmation" in result["name"]

    @pytest.mark.asyncio
    async def test_booking_confirmation_required_info(self):
        """Test that prompt lists required guest information"""
        result = await prompts.booking_confirmation_prompt()

        template = result["template"]
        # Should mention required fields
        required_fields = ["name", "email", "phone", "date"]
        # At least 3 of these should be mentioned
        mentions = sum(1 for field in required_fields if field in template.lower())
        assert mentions >= 3

    @pytest.mark.asyncio
    async def test_booking_confirmation_mentions_tool(self):
        """Test that prompt references reservation tool"""
        result = await prompts.booking_confirmation_prompt()

        template = result["template"]
        assert "create_reservation" in template or "reservation" in template.lower()

    @pytest.mark.asyncio
    async def test_booking_confirmation_emphasizes_accuracy(self):
        """Test that prompt emphasizes confirming details"""
        result = await prompts.booking_confirmation_prompt()

        template = result["template"]
        # Should mention confirmation or verification
        assert "confirm" in template.lower() or "verify" in template.lower() or "correct" in template.lower()


@pytest.mark.unit
class TestPetPolicyPrompt:
    """Test the pet policy inquiry prompt template"""

    @pytest.mark.asyncio
    async def test_pet_policy_structure(self):
        """Test pet policy prompt structure"""
        result = await prompts.pet_policy_inquiry_prompt()

        assert isinstance(result, dict)
        assert "name" in result
        assert "template" in result
        assert "Pet" in result["name"]

    @pytest.mark.asyncio
    async def test_pet_policy_key_information(self):
        """Test that prompt includes key pet policy info"""
        result = await prompts.pet_policy_inquiry_prompt()

        template = result["template"]
        # Should mention pets are welcome
        assert "welcome" in template.lower() or "allowed" in template.lower()
        # Should mention fee
        assert "$20" in template or "20" in template or "fee" in template.lower()

    @pytest.mark.asyncio
    async def test_pet_policy_has_examples(self):
        """Test that pet policy includes example responses"""
        result = await prompts.pet_policy_inquiry_prompt()

        # Should have examples of Q&A
        has_examples = "example" in result or "example_responses" in result
        assert has_examples

    @pytest.mark.asyncio
    async def test_pet_policy_welcoming_tone(self):
        """Test that pet policy is welcoming to pet owners"""
        result = await prompts.pet_policy_inquiry_prompt()

        template = result["template"]
        # Should be welcoming, not restrictive
        assert "welcome" in template.lower()


@pytest.mark.unit
class TestLocalRecommendationsPrompt:
    """Test the local recommendations prompt template"""

    @pytest.mark.asyncio
    async def test_local_recommendations_structure(self):
        """Test local recommendations prompt structure"""
        result = await prompts.local_recommendations_prompt()

        assert isinstance(result, dict)
        assert "name" in result
        assert "template" in result
        assert "Local" in result["name"] or "Recommendations" in result["name"]

    @pytest.mark.asyncio
    async def test_local_recommendations_mentions_resources(self):
        """Test that prompt references resource tools"""
        result = await prompts.local_recommendations_prompt()

        template = result["template"]
        # Should mention using resources
        assert "resource" in template.lower() or "local_area_guide" in template

    @pytest.mark.asyncio
    async def test_local_recommendations_key_attractions(self):
        """Test that prompt mentions key local attractions"""
        result = await prompts.local_recommendations_prompt()

        template = result["template"]
        # Should mention Sunday River or major local attraction
        assert "sunday river" in template.lower() or "ski" in template.lower() or "bethel" in template.lower()

    @pytest.mark.asyncio
    async def test_local_recommendations_enthusiastic_tone(self):
        """Test that recommendations have enthusiastic tone"""
        result = await prompts.local_recommendations_prompt()

        template = result["template"]
        # Should be enthusiastic about the area
        assert "enthusiastic" in template.lower() or "helpful" in template.lower()


@pytest.mark.unit
class TestProblemResolutionPrompt:
    """Test the problem resolution prompt template"""

    @pytest.mark.asyncio
    async def test_problem_resolution_structure(self):
        """Test problem resolution prompt structure"""
        result = await prompts.problem_resolution_prompt()

        assert isinstance(result, dict)
        assert "name" in result
        assert "template" in result
        assert "Problem" in result["name"] or "Resolution" in result["name"]

    @pytest.mark.asyncio
    async def test_problem_resolution_approach(self):
        """Test that prompt outlines resolution approach"""
        result = await prompts.problem_resolution_prompt()

        template = result["template"]
        # Should mention listening, apologizing, solving
        key_elements = ["listen", "apolog", "solution", "resolve"]
        mentions = sum(1 for element in key_elements if element in template.lower())
        assert mentions >= 2

    @pytest.mark.asyncio
    async def test_problem_resolution_empathetic_tone(self):
        """Test that prompt emphasizes empathy"""
        result = await prompts.problem_resolution_prompt()

        template = result["template"]
        assert "empathetic" in template.lower() or "professional" in template.lower()

    @pytest.mark.asyncio
    async def test_problem_resolution_escalation_path(self):
        """Test that prompt includes escalation guidance"""
        result = await prompts.problem_resolution_prompt()

        template = result["template"]
        # Should mention when to escalate
        assert "escalat" in template.lower() or "management" in template.lower() or "staff" in template.lower()

    @pytest.mark.asyncio
    async def test_problem_resolution_has_examples(self):
        """Test that problem resolution includes examples"""
        result = await prompts.problem_resolution_prompt()

        # Should have example responses
        has_examples = "example" in result or "example_responses" in result
        assert has_examples


@pytest.mark.unit
class TestPromptRegistry:
    """Test the prompt registry"""

    def test_prompts_registry_exists(self):
        """Test that PROMPTS registry exists"""
        assert hasattr(prompts, "PROMPTS")
        assert isinstance(prompts.PROMPTS, dict)

    def test_all_prompts_registered(self):
        """Test all expected prompts are in registry"""
        expected_prompts = [
            "guest_greeting",
            "availability_inquiry",
            "booking_confirmation",
            "pet_policy",
            "local_recommendations",
            "problem_resolution"
        ]

        for prompt_name in expected_prompts:
            assert prompt_name in prompts.PROMPTS, f"Prompt {prompt_name} not in registry"

    def test_prompt_functions_are_callable(self):
        """Test all registered prompts are callable"""
        for prompt_name, prompt_func in prompts.PROMPTS.items():
            assert callable(prompt_func), f"Prompt {prompt_name} is not callable"

    @pytest.mark.asyncio
    async def test_all_prompts_return_valid_structure(self):
        """Test that all prompts return valid structure"""
        for prompt_name, prompt_func in prompts.PROMPTS.items():
            # Call with no arguments (some may accept optional args)
            try:
                result = await prompt_func()
            except TypeError:
                # If it requires args, skip (already tested individually)
                continue

            assert isinstance(result, dict), f"Prompt {prompt_name} didn't return dict"
            assert "name" in result or "template" in result, f"Prompt {prompt_name} missing required fields"


@pytest.mark.unit
class TestPromptConsistency:
    """Test consistency across all prompts"""

    @pytest.mark.asyncio
    async def test_all_prompts_have_templates(self):
        """Test that all prompts include template field"""
        prompt_funcs = [
            prompts.guest_greeting_prompt(),
            prompts.availability_inquiry_prompt(),
            prompts.booking_confirmation_prompt(),
            prompts.pet_policy_inquiry_prompt(),
            prompts.local_recommendations_prompt(),
            prompts.problem_resolution_prompt()
        ]

        results = await asyncio.gather(*prompt_funcs)

        for result in results:
            assert "template" in result
            assert isinstance(result["template"], str)
            assert len(result["template"]) > 0

    @pytest.mark.asyncio
    async def test_all_prompts_have_names(self):
        """Test that all prompts include name field"""
        prompt_funcs = [
            prompts.guest_greeting_prompt(),
            prompts.availability_inquiry_prompt(),
            prompts.booking_confirmation_prompt(),
            prompts.pet_policy_inquiry_prompt(),
            prompts.local_recommendations_prompt(),
            prompts.problem_resolution_prompt()
        ]

        results = await asyncio.gather(*prompt_funcs)

        for result in results:
            assert "name" in result
            assert isinstance(result["name"], str)
            assert len(result["name"]) > 0

    @pytest.mark.asyncio
    async def test_templates_are_substantial(self):
        """Test that all templates have substantial content"""
        prompt_funcs = [
            prompts.guest_greeting_prompt(),
            prompts.availability_inquiry_prompt(),
            prompts.booking_confirmation_prompt(),
            prompts.pet_policy_inquiry_prompt(),
            prompts.local_recommendations_prompt(),
            prompts.problem_resolution_prompt()
        ]

        results = await asyncio.gather(*prompt_funcs)

        for result in results:
            template = result["template"]
            # Templates should be meaningful (>50 chars minimum)
            assert len(template) > 50, f"Template too short: {result.get('name', 'unknown')}"

    @pytest.mark.asyncio
    async def test_templates_mention_property(self):
        """Test that templates reference West Bethel Motel"""
        prompt_funcs = [
            prompts.guest_greeting_prompt(),
            prompts.availability_inquiry_prompt(),
            prompts.booking_confirmation_prompt(),
            prompts.pet_policy_inquiry_prompt(),
            prompts.local_recommendations_prompt(),
            prompts.problem_resolution_prompt()
        ]

        results = await asyncio.gather(*prompt_funcs)

        # At least most prompts should mention the property
        mentions_property = sum(
            1 for result in results
            if "west bethel motel" in result["template"].lower() or "motel" in result["template"].lower()
        )
        assert mentions_property >= 4, "Most prompts should mention the property name"


# Import asyncio for gather
import asyncio


# Run tests with: pytest tests/unit/test_stayhive_prompts.py -v
