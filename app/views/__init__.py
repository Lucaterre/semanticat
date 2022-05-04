from .projectHandler import (index,
                                           remove_project)
from .documentHandler import (manage_documents,
                                            import_documents,
                                            remove_document,
                                            remove_documents)
from .workflowHandler import (project,
                                            statistics_ner_project,
                                            new_project_description,
                                            parse_document,
                                            ner,
                                            export_enhanced)
from .configurationHandler import (configuration,
                                                 list_models,
                                                 list_languages,
                                                 list_tagset,
                                                 actual_configuration_ner_recommender_project,
                                                 save_ner_recommender_configuration,
                                                 new_pair,
                                                 save_pair,
                                                 remove_pair)
from .annotationHandler import (workbase_ner,
                                              get_mapping,
                                              get_annotations,
                                              annotations_to_delete,
                                              labels_count,
                                              add_annotation,
                                              add_annotations_from_json,
                                              remove_annotation,
                                              remove_all_annotations,
                                              modify_annotation)
from .errorHandler import (error_404,
                         error_500)
from .appHandler import (clean_db,
                        shutdown)