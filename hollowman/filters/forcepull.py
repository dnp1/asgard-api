#encoding: utf-8

import json
from hollowman.filters import BaseFilter


class ForcePullFilter(BaseFilter):

    name = 'force_pull'

    def run(self, ctx):
        request = ctx.request
        if request.is_json and request.data:
            data = request.get_json()

            if self.is_single_app(data):
                original_app_dict = json.loads(self.get_original_app(ctx).to_json())
                original_app_dict.update(data)

                if 'labels' in original_app_dict and ('hollowman.filter.forcepull.disable' in original_app_dict['labels']):
                    value = False
                else:
                    value = True

                original_app_dict['container']['docker']["forcePullImage"] = value

                request.data = json.dumps(original_app_dict)

        return request
