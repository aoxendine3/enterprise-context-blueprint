import {defineBlueprint, defineDocumentFunction} from '@sanity/blueprints'

export default defineBlueprint({
  resources: [
    defineDocumentFunction({
      name: 'xoras-sovereign-doc-verifier',
      event: {
        on: ['create', 'update'],
        filter: '_type == "sovereign_document"'
      }
    }),
    defineDocumentFunction({
      name: 'xoras-audit-receipt-logger',
      event: {
        on: ['create'],
        filter: '_type == "audit_receipt"'
      }
    }),
    defineDocumentFunction({
      name: 'xoras-golden-question-evaluator',
      event: {
        on: ['create', 'update'],
        filter: '_type == "golden_question"'
      }
    })
  ]
})