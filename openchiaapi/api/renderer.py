from rest_framework.renderers import BrowsableAPIRenderer


# This is so we dont leak private data in forms
class NoHTMLFormBrowsableAPIRenderer(BrowsableAPIRenderer):

    def get_rendered_html_form(self, data, view, method, request):
        if request.path.endswith('/giveaway/closest'):
            return super().get_rendered_html_form(data, view, method, request)
        return ''

    def get_raw_data_form(self, data, view, method, request):
        return
