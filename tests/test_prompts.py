# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from tests.utils import get_test_data_path
from knowledge.markdown import KnowledgeBaseMarkdown
from prompts.prompts import PromptList
from unittest.mock import MagicMock


TEST_KNOWLEDGE_PACK_PATH = get_test_data_path() + "/test_knowledge_pack"
ACTIVE_KNOWLEDGE_CONTEXT = "context_a"
CONTEXT_B = "context_b"


def create_knowledge_manager():
    return MagicMock()


def create_knowledge_base(knowledge_pack_path):
    knowledge_base = KnowledgeBaseMarkdown()
    knowledge_base.load_for_context(
        ACTIVE_KNOWLEDGE_CONTEXT,
        knowledge_pack_path + "/contexts/" + ACTIVE_KNOWLEDGE_CONTEXT + ".md",
    )
    knowledge_base.load_for_context(
        CONTEXT_B,
        knowledge_pack_path + "/contexts/" + CONTEXT_B + ".md",
    )
    return knowledge_base


def test_init_should_load_files():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    assert len(prompt_list.prompts) == 7


def test_init_should_exclude_readmes():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    assert len(prompt_list.prompts) == 7


def test_init_should_set_defaults_for_metadata():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    prompt_to_assert = next(
        filter(
            lambda prompt: prompt.metadata["identifier"] == "uuid-0",
            prompt_list.prompts,
        ),
        None,
    )
    assert prompt_to_assert.metadata["title"] == "Test0"
    assert prompt_to_assert.metadata["categories"] == []
    assert prompt_to_assert.metadata["type"] == "chat"
    assert prompt_to_assert.metadata["editable"] is False
    assert prompt_to_assert.metadata["show"] is True


def test_get_should_return_prompt_data():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    prompt = prompt_list.get("uuid-1")
    assert prompt.metadata["title"] == "Test1"


def test_create_template():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    template = prompt_list.create_template("uuid-3")
    assert template.template == "Content: {user_input} | Business: {context}"


def test_create_and_render_template_for_given_multiple_knowledge_pack_contexts():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )

    rendered, template = prompt_list.create_and_render_template(
        [ACTIVE_KNOWLEDGE_CONTEXT, CONTEXT_B],
        "uuid-3",
        {"user_input": "Some User Input"},
    )

    knowledge_manager.add_complete_context.assert_called_once()
    knowledge_manager.add_complete_context.assert_called_with(
        "Domain knowledge from context_a\n\ncontext_b domain knowledge"
    )
    assert template.template == "Content: {user_input} | Business: {context}"
    expected_rendered_output = "Content: Some User Input | Business: Domain knowledge from context_a\n\ncontext_b domain knowledge"
    assert rendered == expected_rendered_output


def test_create_and_render_template_for_given_user_context_without_knowledge_pack_context():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, template = prompt_list.create_and_render_template(
        None,
        "uuid-3",
        {"user_input": "Some User Input"},
        user_context="some user context",
    )
    knowledge_manager.add_complete_context.assert_called_once()
    knowledge_manager.add_complete_context.assert_called_with("some user context")
    assert template.template == "Content: {user_input} | Business: {context}"
    expected_rendered_output = "Content: Some User Input | Business: some user context"
    assert rendered == expected_rendered_output


def test_create_and_render_template_for_given_user_context_without_knowledge_pack_context_and_user_context():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, template = prompt_list.create_and_render_template(
        None,
        "uuid-3",
        {"user_input": "Some User Input"},
    )
    knowledge_manager.add_complete_context.assert_not_called()


def test_create_and_render_template_with_missing_variables():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, _ = prompt_list.create_and_render_template(
        None,
        "uuid-3",
        {"user_input": "Some User Input"},
    )
    assert (
        rendered
        == "Content: Some User Input | Business: None provided, please try to help without this information."
    )


def test_create_and_render_template_overwrite_knowledge_base():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, _ = prompt_list.create_and_render_template(
        [ACTIVE_KNOWLEDGE_CONTEXT],
        "uuid-3",
        {"user_input": "Some User Input", "context": "Overwritten Business"},
    )
    assert rendered == "Content: Some User Input | Business: Overwritten Business"


def test_render_prompt_with_additional_vars():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, _ = prompt_list.render_prompt(
        [ACTIVE_KNOWLEDGE_CONTEXT],
        "uuid-4",
        "Some User Input",
        {"additional": "Additional Var"},
        user_context="some user context",
    )
    assert rendered == "Content Some User Input Additional Var"


def test_render_prompt_for_given_prompt_id_and_knowledge_pack_context():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, _ = prompt_list.render_prompt(
        [ACTIVE_KNOWLEDGE_CONTEXT],
        "uuid-6",
        "Some User Input",
    )

    assert rendered == """Content Some User Input Domain knowledge from context_a"""


def test_render_prompt_for_given_prompt_id_and_user_context():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, _ = prompt_list.render_prompt(
        [ACTIVE_KNOWLEDGE_CONTEXT],
        "uuid-6",
        "Some User Input",
        user_context="some user context",
    )

    assert (
        rendered
        == """Content Some User Input Domain knowledge from context_a\n\nsome user context"""
    )


def test_filter_should_filter_by_one_category_and_include_without_category():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    prompt_list.filter(["architecture"])
    assert len(prompt_list.prompts) == 4


def test_filter_should_filter_by_multiple_categories():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    prompt_list.filter(["architecture", "coding"])
    assert len(prompt_list.prompts) == 5


def test_render_prompt_without_prompt_choice():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    rendered, _ = prompt_list.render_prompt(
        [ACTIVE_KNOWLEDGE_CONTEXT], None, "Some User Input"
    )
    assert rendered == ""


def test_create_markdown_summary():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    markdown_summary = prompt_list.render_prompts_summary_markdown()

    expected_summary = (
        "- **Test4**: Prompt description 4\n" "- **Test5**: Prompt description 5\n"
    )

    assert expected_summary in markdown_summary


def test_get_prompts_with_follow_ups():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    prompts_with_follow_ups = prompt_list.get_prompts_with_follow_ups()

    # test knowledge pack configures 2 valid follow up prompts for uuid-1

    uuid_1_entry = [
        prompt for prompt in prompts_with_follow_ups if prompt["identifier"] == "uuid-1"
    ][0]
    assert uuid_1_entry is not None
    assert len(uuid_1_entry["follow_ups"]) == 2
    assert uuid_1_entry["follow_ups"][0]["identifier"] == "uuid-2"
    assert uuid_1_entry["follow_ups"][0]["title"] == "Test2"
    assert "prompt 2" in uuid_1_entry["follow_ups"][0]["help_prompt_description"]
    assert uuid_1_entry["follow_ups"][1]["identifier"] == "uuid-3"
    assert uuid_1_entry["follow_ups"][1]["title"] == "Test3"
    assert "prompt 3" in uuid_1_entry["follow_ups"][1]["help_prompt_description"]

    uuid_3_entry = [
        prompt for prompt in prompts_with_follow_ups if prompt["identifier"] == "uuid-3"
    ][0]
    assert uuid_3_entry is not None
    assert uuid_3_entry["follow_ups"] == []


def test_get_prompts_with_follow_ups_invalid_prompt_id():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()

    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )
    prompts_with_follow_ups = prompt_list.get_prompts_with_follow_ups()

    # test knowledge pack configures invalid follow-up and valid follow-up for uuid-2

    uuid_2_entry = [
        prompt for prompt in prompts_with_follow_ups if prompt["identifier"] == "uuid-2"
    ][0]
    assert uuid_2_entry is not None
    assert len(uuid_2_entry["follow_ups"]) == 1
    assert uuid_2_entry["follow_ups"][0]["identifier"] == "uuid-3"


def test_append_user_context_if_knowledge_pack_key_value_is_None():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )

    user_context = "additional context"

    result = prompt_list.appendUserContext(None, user_context)

    assert result["context"] == "additional context"


def test_append_user_context_if_knowledge_pack_context_exists():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )

    knowledge_and_input = {"context": "Initial context"}
    user_context = "additional context"

    result = prompt_list.appendUserContext(knowledge_and_input, user_context)

    assert result["context"] == "Initial context\n\nadditional context"


def test_should_not_append_user_context_if_user_context_doesnt_exists():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )

    knowledge_and_input = {"context": "Initial context"}
    user_context = None

    result = prompt_list.appendUserContext(knowledge_and_input, user_context)

    assert result["context"] == "Initial context"


def test_append_user_context_if_knowledge_pack_context_key_doesnt_exist():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )

    knowledge_and_input = {}
    user_context = "Additional context"

    result = prompt_list.appendUserContext(knowledge_and_input, user_context)

    assert result["context"] == "Additional context"


def test_get_rendered_context_with_user_context():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )

    rendered_context = prompt_list.get_rendered_context(
        None, "uuid-3", "some user context"
    )

    expected_context = "some user context"
    assert rendered_context == expected_context


def test_get_rendered_context_with_knowledge_pack_context():
    knowledge_base = create_knowledge_base(TEST_KNOWLEDGE_PACK_PATH)
    knowledge_manager = create_knowledge_manager()
    prompt_list = PromptList(
        "chat", knowledge_base, knowledge_manager, root_dir=TEST_KNOWLEDGE_PACK_PATH
    )

    rendered_context = prompt_list.get_rendered_context(
        [ACTIVE_KNOWLEDGE_CONTEXT], "uuid-3", None
    )

    expected_context = "Domain knowledge from context_a"
    assert rendered_context == expected_context
