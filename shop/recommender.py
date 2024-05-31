import redis
from django.conf import settings

from .models import Product

# Redis 연결
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

class Recommender:
    def get_product_key(self, id):
        return f'product:{id}:purchased_with'

    def products_bought(self, products):
        product_ids = [p.id for p in products]

        for product_id in product_ids:
            for with_id in product_ids:
                # 각 제품과 함께 구매한 다른 제품 획득
                if product_id != with_id:
                    # 함께 구매한 제품의 점수 증가
                    r.zincrby(self.get_product_key(product_id), 1, with_id)

    def suggest_products_for(self, products, max_results=6):
        product_ids = [p.id for p in products]

        if len(products) == 1:
            suggestions = r.zrange(self.get_product_key(product_ids[0]),
                                   0, -1, desc=True)[:max_results]
        else:
            # 임시 키 생성
            flat_ids = ''.join([str(id) for id in product_ids])
            tmp_key = f'tmp_{flat_ids}'
            # 주어진 각 제품들에 함께 구매한 제품들의 점수 합산
            # 결과가 정렬된 세트를 임시 키에 저장
            keys = [self.get_product_key(id) for id in product_ids]
            r.zunionstore(tmp_key, keys)
            # 처음에 주어진 제품들의 ID를 추천 목록에서 제거
            r.zrem(tmp_key, *product_ids)
            # 점수를 기준으로 역정렬해서 제품 ID 목록을 가져옴
            suggestions = r.zrange(tmp_key, 0, -1, desc=True)[:max_results]
            # 임시 키 제거
            r.delete(tmp_key)

        suggested_products_ids = [int(id) for id in suggestions]
        # 추천 제품 정보 조회 및 순서대로 정렬해 표시
        suggested_products = list(Product.objects.filter(id__in=suggested_products_ids))
        suggested_products.sort(key=lambda x: suggested_products_ids.index(x.id))

        return suggested_products

    def clear_purchases(self):
        for id in Product.objects.values_list('id', flat=True):
            r.delete(self.get_product_key(id))