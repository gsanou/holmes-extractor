import unittest
import holmes_extractor as holmes
from holmes_extractor.extensive_matching import TopicMatcher
import os

script_directory = os.path.dirname(os.path.realpath(__file__))
ontology = holmes.Ontology(os.sep.join((script_directory,'test_ontology.owl')))
holmes_manager_coref = holmes.Manager(model='en_core_web_lg', ontology=ontology,
        overall_similarity_threshold=0.65, perform_coreference_resolution=True)
holmes_manager_coref_embedding_on_root = holmes.Manager(model='en_core_web_lg', ontology=ontology,
        overall_similarity_threshold=0.65, embedding_based_matching_on_root_words=True)
holmes_manager_coref_no_embeddings = holmes.Manager(model='en_core_web_lg', ontology=ontology,
        overall_similarity_threshold=1, perform_coreference_resolution=True)

class EnglishTopicMatchingTest(unittest.TestCase):

    def _check_equals(self, text_to_match, document_text, highest_score, manager):
        manager.remove_all_documents()
        manager.parse_and_register_document(document_text)
        topic_matches = manager.topic_match_documents_against(text_to_match, relation_score=20,
                reverse_only_relation_score=15, single_word_score=10, single_word_any_tag_score=5)
        self.assertEqual(int(topic_matches[0].score), highest_score)

    def test_direct_matching(self):
        self._check_equals("A plant grows", "A plant grows", 34, holmes_manager_coref)

    def test_direct_matching_nonsense_word(self):
        self._check_equals("My friend visited gegwghg", "Peter visited gegwghg", 34,
                holmes_manager_coref)

    def test_dative_matching(self):
        self._check_equals("I gave Peter a dog", "I gave Peter a present", 34, holmes_manager_coref)

    def test_coref_matching(self):
        self._check_equals("A plant grows", "I saw a plant. It was growing", 34,
                holmes_manager_coref)

    def test_entity_matching(self):
        self._check_equals("My friend visited ENTITYGPE", "Peter visited Paris", 34,
                holmes_manager_coref)

    def test_entitynoun_matching(self):
        self._check_equals("My friend visited ENTITYNOUN", "Peter visited a city", 25,
                holmes_manager_coref)

    def test_ontology_matching(self):
        self._check_equals("I saw an animal", "Somebody saw a cat", 34,
                holmes_manager_coref)

    def test_ontology_matching_word_only(self):
        self._check_equals("I saw an animal", "Somebody chased a cat", 10,
                holmes_manager_coref)

    def test_embedding_matching_not_root(self):
        self._check_equals("I saw a king", "Somebody saw a queen", 22,
                holmes_manager_coref)

    def test_embedding_matching_root(self):
        self._check_equals("I saw a king", "Somebody saw a queen", 28,
                holmes_manager_coref_embedding_on_root)

    def test_embedding_matching_root_word_only(self):
        self._check_equals("king", "queen", 7,
                holmes_manager_coref_embedding_on_root)

    def test_matching_only_adjective(self):
        self._check_equals("nice", "nice", 5, holmes_manager_coref)

    def test_matching_only_adjective_where_noun(self):
        self._check_equals("nice place", "nice", 5, holmes_manager_coref)

    def test_stopwords(self):
        self._check_equals("The donkey has a roof", "The donkey has a roof", 19,
                holmes_manager_coref)

    def test_stopwords_control(self):
        self._check_equals("The donkey paints a roof", "The donkey paints a roof", 87,
                holmes_manager_coref)

    def test_reverse_matching_noun_no_coreference(self):
        self._check_equals("A car with an engine", "An automobile with an engine", 61,
                holmes_manager_coref)

    def test_reverse_matching_noun_no_coreference_control_no_embeddings(self):
        self._check_equals("A car with an engine", "An automobile with an engine", 29,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_noun_no_coreference_control_same_word(self):
        self._check_equals("A car with an engine", "A car with an engine", 79,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_suppressed_with_embedding_based_retries(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.parse_and_register_document("An automobile with an engine")
        topic_matches = holmes_manager_coref.topic_match_documents_against("A car with an engine",
                relation_score=20, reverse_only_relation_score=15, single_word_score=10,
                single_word_any_tag_score=5,
                maximum_number_of_single_word_matches_for_embedding_based_retries = 0)
        self.assertEqual(int(topic_matches[0].score), 29)

    def test_reverse_matching_suppressed_with_preexisting_match_cutoff(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.parse_and_register_document("An automobile with an engine")
        topic_matches = holmes_manager_coref.topic_match_documents_against("A car with an engine",
                relation_score=20, reverse_only_relation_score=15, single_word_score=10,
                single_word_any_tag_score=5,
                embedding_based_retry_preexisting_match_cutoff = 0.0)
        self.assertEqual(int(topic_matches[0].score), 29)

    def test_reverse_matching_noun_coreference_on_governor(self):
        self._check_equals("A car with an engine", "I saw an automobile. I saw it with an engine",
                60,
                holmes_manager_coref)

    def test_reverse_matching_noun_coreference_on_governor_control_no_embeddings(self):
        self._check_equals("A car with an engine", "I saw an automobile. I saw it with an engine",
                29,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_noun_coreference_on_governor_control_same_word(self):
        self._check_equals("A car with an engine", "I saw a car. I saw it with an engine",
                77,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_noun_coreference_on_governed(self):
        self._check_equals(
                "An engine with a car", "I saw an automobile. There was an engine with it", 31,
                holmes_manager_coref)

    def test_reverse_matching_noun_coreference_on_governed_control_no_embeddings(self):
        self._check_equals(
                "An engine with a car", "I saw an automobile. There was an engine with it", 14,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_noun_coreference_on_governed_control_same_word(self):
        self._check_equals(
                "An engine with a car", "I saw a car. There was an engine with it", 85,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_verb(self):
        self._check_equals("A company is bought", "A company is purchased", 27,
                holmes_manager_coref)

    def test_reverse_matching_verb_control_no_embeddings(self):
        self._check_equals("A company is bought", "A company is purchased", 10,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_verb_control_same_word(self):
        self._check_equals("A company is bought", "A company is bought", 34,
                holmes_manager_coref_no_embeddings)

    def test_reverse_matching_verb_with_coreference_and_conjunction(self):
        self._check_equals("A company is bought", "A company is bought and purchased", 34,
                holmes_manager_coref)

    def test_reverse_matching_leading_to_new_forward_matching(self):
        self._check_equals("Somebody buys a van and a car",
                "Somebody purchases a van and an automobile", 59,
                holmes_manager_coref)

    def test_reverse_matching_leading_to_new_forward_matching_link_word_also_similar(self):
        self._check_equals("Somebody buys a vehicle and a car",
                "Somebody purchases a vehicle and an automobile", 84,
                holmes_manager_coref)
            # more than in example above because car and vehicle are more similar
            # than car and automobile

    def test_reverse_matching_leading_to_new_forward_matching_control(self):
        self._check_equals("Somebody buys a van and a car",
                "Somebody purchases a van and a pig", 27,
                holmes_manager_coref)

    def test_two_matches_on_same_document_tokens_because_of_embeddings(self):
        self._check_equals("Somebody buys a vehicle",
                "Somebody buys a vehicle and a car", 34,
                holmes_manager_coref)

    def test_reverse_matching_only(self):
        self._check_equals("with an idea",
                "with an idea", 29,
                holmes_manager_coref)

    def test_repeated_single_word_label_tags_matched(self):
        self._check_equals("dog",
                "a dog and a dog", 10,
                holmes_manager_coref)

    def test_repeated_single_word_label_tags_not_matched(self):
        self._check_equals("in",
                "in and in", 5,
                holmes_manager_coref)

    def test_repeated_relation_label_not_reverse_only_no_common_term(self):
        self._check_equals("a big dog",
                "a big dog and a big dog", 48,
                holmes_manager_coref)

    def test_repeated_relation_label_not_reverse_only_common_term(self):
        self._check_equals("a big dog",
                "a big and big dog", 34,
                holmes_manager_coref)

    def test_repeated_relation_label_reverse_only_no_common_term(self):
        self._check_equals("in Germany",
                "in Germany and in Germany", 43,
                holmes_manager_coref)

    def test_repeated_relation_label_reverse_only_common_term(self):
        self._check_equals("in Germany",
                "in Germany and Germany", 29,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_and_in_document_not_root(self):
        self._check_equals("Richard Paul Hudson came",
                "I saw Richard Paul Hudson", 24,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_single_word_in_document_not_root(self):
        self._check_equals("Hudson came",
                "I saw Richard Paul Hudson", 10,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_dependent_words_in_document_not_root(self):
        self._check_equals("Richard Paul came",
                "I saw Richard Paul Hudson", 9,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_multiword_in_document_with_coref_not_root(self):
        self._check_equals("Richard Paul Hudson came",
                "I saw Richard Paul Hudson. He came", 48,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_multiword_in_document_with_noun_coref_not_root(self):
        self._check_equals("Richard Paul Hudson came",
                "I saw Richard Paul Hudson. Hudson came", 48,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_single_in_document_with_coref_not_root(self):
        self._check_equals("Hudson came",
                "I saw Richard Paul Hudson. He came", 34,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_and_in_document_root(self):
        self._check_equals("the tired Richard Paul Hudson",
                "I saw Richard Paul Hudson", 24,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_single_word_in_document_root(self):
        self._check_equals("the tired Hudson",
                "I saw Richard Paul Hudson", 10,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_dependent_words_in_document_root(self):
        self._check_equals("the tired Richard Paul",
                "I saw Richard Paul Hudson", 9,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_multiword_in_document_with_coref_root(self):
        self._check_equals("the tired Richard Paul Hudson",
                "I saw Richard Paul Hudson. He came", 24,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_single_in_document_with_coref_root(self):
        self._check_equals("the tired Hudson came",
                "I saw Richard Paul Hudson. He came", 34,
                holmes_manager_coref)

    def test_multiword_in_text_to_search_and_in_document_not_root_match_on_embeddings(self):
        self._check_equals("Richard Paul Hudson came",
                "I saw Richard Paul Hudson", 27,
                holmes_manager_coref_embedding_on_root)

    def test_multiword_in_text_to_search_and_in_document_root_match_on_embeddings(self):
        self._check_equals("the tired Richard Paul Hudson",
                "I saw Richard Paul Hudson", 27,
                holmes_manager_coref_embedding_on_root)

    def test_multiword_in_text_to_search_and_in_document_not_root_no_embeddings(self):
        self._check_equals("Richard Paul Hudson came",
                "I saw Richard Paul Hudson", 27,
                holmes_manager_coref_embedding_on_root)

    def test_multiword_in_text_to_search_and_in_document_root_no_embeddings(self):
        self._check_equals("the tired Richard Paul Hudson",
                "I saw Richard Paul Hudson", 27,
                holmes_manager_coref_embedding_on_root)

    def test_coreference_double_match_on_governed(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.parse_and_register_document(
                "I saw a man. The man walked")
        topic_matches = holmes_manager_coref.topic_match_documents_against("A man walks",
                relation_score=20, single_word_score=10, single_word_any_tag_score=5)
        self.assertEqual(int(topic_matches[0].score), 34)
        self.assertEqual(topic_matches[0].sentences_start_index, 5)
        self.assertEqual(topic_matches[0].sentences_end_index, 7)
        self.assertEqual(topic_matches[0].start_index, 6)
        self.assertEqual(topic_matches[0].end_index, 7)
        self.assertEqual(topic_matches[0].relative_start_index, 1)
        self.assertEqual(topic_matches[0].relative_end_index, 2)

    def test_coreference_double_match_on_governor(self):
        self._check_equals("A big man", "I saw a big man. The man walked", 34, holmes_manager_coref)
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.parse_and_register_document(
                "I saw a big man. The man walked")
        topic_matches = holmes_manager_coref.topic_match_documents_against("A big man", relation_score=20, single_word_score=10, single_word_any_tag_score=5)
        self.assertEqual(int(topic_matches[0].score), 34)
        self.assertEqual(topic_matches[0].sentences_start_index, 0)
        self.assertEqual(topic_matches[0].sentences_end_index, 8)
        self.assertEqual(topic_matches[0].start_index, 3)
        self.assertEqual(topic_matches[0].end_index, 7)
        self.assertEqual(topic_matches[0].relative_start_index, 3)
        self.assertEqual(topic_matches[0].relative_end_index, 7)

    def test_indexes(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.parse_and_register_document(
                "This is an irrelevant sentence. I think a plant grows.")
        topic_matches = holmes_manager_coref.topic_match_documents_against("A plant grows")
        self.assertEqual(topic_matches[0].sentences_start_index, 6)
        self.assertEqual(topic_matches[0].sentences_end_index, 11)
        self.assertEqual(topic_matches[0].start_index, 9)
        self.assertEqual(topic_matches[0].end_index, 10)
        self.assertEqual(topic_matches[0].relative_start_index, 3)
        self.assertEqual(topic_matches[0].relative_end_index, 4)

    def test_indexes_with_preceding_non_matched_dependent(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.parse_and_register_document(
                "I saw a big dog.")
        topic_matches = holmes_manager_coref.topic_match_documents_against("A big dog")
        self.assertEqual(topic_matches[0].sentences_start_index, 0)
        self.assertEqual(topic_matches[0].sentences_end_index, 5)
        self.assertEqual(topic_matches[0].start_index, 3)
        self.assertEqual(topic_matches[0].end_index, 4)
        self.assertEqual(topic_matches[0].relative_start_index, 3)
        self.assertEqual(topic_matches[0].relative_end_index, 4)

    def test_indexes_with_subsequent_non_matched_dependent(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.parse_and_register_document(
                "The dog I saw was big.")
        topic_matches = holmes_manager_coref.topic_match_documents_against("A big dog")
        self.assertEqual(topic_matches[0].sentences_start_index, 0)
        self.assertEqual(topic_matches[0].sentences_end_index, 6)
        self.assertEqual(topic_matches[0].start_index, 1)
        self.assertEqual(topic_matches[0].end_index, 5)
        self.assertEqual(topic_matches[0].relative_start_index, 1)
        self.assertEqual(topic_matches[0].relative_end_index, 5)

    def test_additional_search_phrases(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.remove_all_search_phrases()
        holmes_manager_coref.parse_and_register_document(
                "Peter visited Paris and a dog chased a cat. Beef and lamb and pork.")
        doc = holmes_manager_coref.semantic_analyzer.parse("My friend visited ENTITYGPE")
        phraselet_labels_to_search_phrases = {}
        holmes_manager_coref.structural_matcher.add_phraselets_to_dict(doc,
                phraselet_labels_to_search_phrases=phraselet_labels_to_search_phrases,
                replace_with_hypernym_ancestors=False,
                match_all_words=False,
                returning_serialized_phraselets=False,
                ignore_relation_phraselets=False,
                include_reverse_only=False)
        holmes_manager_coref.structural_matcher.register_search_phrase("A dog chases a cat", None)
        holmes_manager_coref.structural_matcher.register_search_phrase("beef", None)
        holmes_manager_coref.structural_matcher.register_search_phrase("lamb", None)
        position_sorted_structural_matches = sorted(holmes_manager_coref.structural_matcher.
                        match_documents_against_search_phrase_list(
                        phraselet_labels_to_search_phrases.values(),False),
                        key=lambda match: (match.document_label, match.index_within_document))
        topic_matcher = TopicMatcher(holmes_manager_coref,
                maximum_activation_distance=75,
                relation_score=20,
                reverse_only_relation_score=15,
                single_word_score=5,
                single_word_any_tag_score=2,
                overlapping_relation_multiplier=1.5,
                overlap_memory_size=10,
                maximum_activation_value=1000,
                sideways_match_extent=100,
                only_one_result_per_document=False,
                number_of_results=1)
        score_sorted_structural_matches = topic_matcher.perform_activation_scoring(
                position_sorted_structural_matches)
        topic_matches = topic_matcher.get_topic_matches(score_sorted_structural_matches,
                position_sorted_structural_matches)
        self.assertEqual(topic_matches[0].start_index, 1)
        self.assertEqual(topic_matches[0].end_index, 2)

    def test_only_one_result_per_document(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.remove_all_search_phrases()
        holmes_manager_coref.parse_and_register_document(
                """
                Peter came home. A great deal of irrelevant text. A great deal of irrelevant text.
                A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
                irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
                A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
                irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
                A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
                irrelevant text. Peter came home.
                """)
        self.assertEqual(len(holmes_manager_coref.topic_match_documents_against("Peter")), 2)
        self.assertEqual(len(holmes_manager_coref.topic_match_documents_against("Peter",
                only_one_result_per_document=True)), 1)

    def test_match_cutoff(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.remove_all_search_phrases()
        holmes_manager_coref.parse_and_register_document(
                """
                A cat.
                A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
                irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
                A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
                irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
                A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
                irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
                The dog chased the cat.
                """)
        topic_matches = holmes_manager_coref.topic_match_documents_against(
                "The dog chased the cat")
        self.assertEqual(topic_matches[0].start_index, 117)
        self.assertEqual(topic_matches[0].end_index, 120)

    def test_result_ordering_by_match_length_different_documents(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.remove_all_search_phrases()
        holmes_manager_coref.parse_and_register_document("""
        A dog chased a cat.
        A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
        irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
        A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
        irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
        A great deal of irrelevant text. A great deal of irrelevant text. A great deal of
        irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text.
        A dog chased a cat. A cat
        """)
        topic_matches = holmes_manager_coref.topic_match_documents_against(
                "The dog chased the cat")
        self.assertEqual(topic_matches[0].end_index - topic_matches[0].start_index, 7)
        self.assertEqual(topic_matches[1].end_index - topic_matches[1].start_index, 4)

    def test_dictionaries(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.remove_all_search_phrases()
        holmes_manager_coref.parse_and_register_document("A dog chased a cat. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A great deal of irrelevant text. A dog chased a cat. A cat. Another irrelevant sentence.")
        holmes_manager_coref.parse_and_register_document("Dogs and cats.",
                "animals")
        topic_match_dictionaries = \
                holmes_manager_coref.topic_match_documents_returning_dictionaries_against(
                "The dog chased the cat")
        self.assertEqual(topic_match_dictionaries,
        [{'document_label': '', 'text': 'A dog chased a cat. A cat.', 'rank': '1=', 'sentences_character_start_index_in_document': 515, 'sentences_character_end_index_in_document': 541, 'finding_character_start_index_in_sentences': 2, 'finding_character_end_index_in_sentences': 25, 'score': 101.74933333333334}, {'document_label': '', 'text': 'A dog chased a cat.', 'rank': '1=', 'sentences_character_start_index_in_document': 0, 'sentences_character_end_index_in_document': 19, 'finding_character_start_index_in_sentences': 2, 'finding_character_end_index_in_sentences': 18, 'score': 101.74933333333334}, {'document_label': 'animals', 'text': 'Dogs and cats.', 'rank': '3', 'sentences_character_start_index_in_document': 0, 'sentences_character_end_index_in_document': 14, 'finding_character_start_index_in_sentences': 0, 'finding_character_end_index_in_sentences': 13, 'score': 9.866666666666667}])
        topic_match_dictionaries = \
                holmes_manager_coref.topic_match_documents_returning_dictionaries_against(
                "The dog chased the cat", tied_result_quotient=0.01)
        self.assertEqual(topic_match_dictionaries,
        [{'document_label': '', 'text': 'A dog chased a cat. A cat.', 'rank': '1=', 'sentences_character_start_index_in_document': 515, 'sentences_character_end_index_in_document': 541, 'finding_character_start_index_in_sentences': 2, 'finding_character_end_index_in_sentences': 25, 'score': 101.74933333333334}, {'document_label': '', 'text': 'A dog chased a cat.', 'rank': '1=', 'sentences_character_start_index_in_document': 0, 'sentences_character_end_index_in_document': 19, 'finding_character_start_index_in_sentences': 2, 'finding_character_end_index_in_sentences': 18, 'score': 101.74933333333334}, {'document_label': 'animals', 'text': 'Dogs and cats.', 'rank': '1=', 'sentences_character_start_index_in_document': 0, 'sentences_character_end_index_in_document': 14, 'finding_character_start_index_in_sentences': 0, 'finding_character_end_index_in_sentences': 13, 'score': 9.866666666666667}])

    def test_result_ordering_by_match_length_different_documents(self):
        holmes_manager_coref.remove_all_documents()
        holmes_manager_coref.remove_all_search_phrases()
        holmes_manager_coref.parse_and_register_document("A dog chased a cat.",'1')
        holmes_manager_coref.parse_and_register_document("A dog chased a cat. A cat.",'2')
        topic_matches = holmes_manager_coref.topic_match_documents_against(
                "The dog chased the cat")
        self.assertEqual(topic_matches[0].end_index, 7)
        self.assertEqual(topic_matches[1].end_index, 4)
