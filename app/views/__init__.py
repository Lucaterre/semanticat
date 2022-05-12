from .project_handler import (index,
                              remove_project)
from .document_handler import (manage_documents,
                               import_documents,
                               remove_document,
                               remove_documents)
from .workflow_handler import (project,
                               statistics_ner_project,
                               new_project_description,
                               parse_document,
                               ner,
                               export_enhanced)
from .configuration_handler import (configuration,
                                    list_models,
                                    list_languages,
                                    list_tagset,
                                    actual_configuration_ner_recommender_project,
                                    save_ner_recommender_configuration,
                                    new_pair,
                                    save_pair,
                                    remove_pair)
from .annotation_handler import (workbase_ner,
                                 get_mapping,
                                 get_annotations,
                                 annotations_to_delete,
                                 labels_count,
                                 add_annotation,
                                 add_annotations_from_json,
                                 remove_annotation,
                                 remove_all_annotations,
                                 modify_annotation)
from .error_handler import (error_404,
                            error_500)
from .app_handler import (clean_db,
                          shutdown)