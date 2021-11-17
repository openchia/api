from rest_framework.renderers import BrowsableAPIRenderer


class NoHTMLFormBrowsableAPIRenderer(BrowsableAPIRenderer):

    def get_rendered_html_form(self, *args, **kwargs):
        return ''

    def get_raw_data_form(self, data, view, method, request):
        return
