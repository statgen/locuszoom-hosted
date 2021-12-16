<script>
    // Custom interactivity associated with the "Upload your own GWAS" page.
    // This enhances just one part of the upload form.
    import GwasParserOptions from 'localzoom/src/components/GwasParserOptions.vue';

    export default {
        name: 'gwas_upload',
        props: ['file_reader', 'show_modal'],
        methods: {
            closeModal() {
                // Close without setting options
                // here
                this.$root.$emit('close');
            },
            sendConfig(parser_options, state) {
                // Close with options selected
                this.$root.$emit('has_options', parser_options);
            }
        },
        components: { GwasParserOptions },
    }
</script>

<template>
  <div>
    <gwas-parser-options v-if="show_modal"
                  :file_reader="file_reader"
                  @ready="sendConfig"
                  @close="closeModal"></gwas-parser-options>
  </div>
</template>

<style scoped>
</style>
