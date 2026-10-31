from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calc.selectors import get_estimate
from apps.cart import selectors, services
from apps.cart.api.serializers import (
    AddItemSerializer,
    CartSerializer,
    UpdateItemSerializer,
    cart_to_dict,
)
from apps.customers.selectors import is_master


def _response(request, cart, code=status.HTTP_200_OK) -> Response:
    view = selectors.cart_view(cart, master=is_master(request))
    return Response(cart_to_dict(view), status=code)


class CartCreateView(APIView):
    @extend_schema(request=None, responses={201: CartSerializer})
    def post(self, request):
        return _response(request, services.create_cart(), status.HTTP_201_CREATED)


class CartDetailView(APIView):
    @extend_schema(responses=CartSerializer)
    def get(self, request, token: str):
        return _response(request, selectors.get_cart(token))


class CartItemsView(APIView):
    @extend_schema(request=AddItemSerializer, responses={201: CartSerializer})
    def post(self, request, token: str):
        cart = selectors.get_cart(token)
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.add_item(cart, **serializer.validated_data)
        return _response(request, cart, status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    @extend_schema(request=UpdateItemSerializer, responses=CartSerializer)
    def patch(self, request, token: str, item_id: int):
        cart = selectors.get_cart(token)
        serializer = UpdateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_item(cart, item_id, serializer.validated_data["qty"])
        return _response(request, cart)

    @extend_schema(responses=CartSerializer)
    def delete(self, request, token: str, item_id: int):
        cart = selectors.get_cart(token)
        services.remove_item(cart, item_id)
        return _response(request, cart)


class CartFromEstimateView(APIView):
    @extend_schema(request=None, responses={201: CartSerializer})
    def post(self, request, token: str, code: str):
        cart = selectors.get_cart(token)
        services.add_from_estimate(cart, get_estimate(code))
        return _response(request, cart, status.HTTP_201_CREATED)
