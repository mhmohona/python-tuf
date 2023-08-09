# Copyright the TUF contributors
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Extract and verify TUF payloads from different signature wrappers.

"""
import abc
from typing import Dict, Optional, Tuple, Type, Union

from securesystemslib.signer import Signature

from tuf.api import exceptions
from tuf.api._payload import Root, T, Targets
from tuf.api.metadata import Metadata

Delegator = Union[Root, Targets]


class Unwrapper(metaclass=abc.ABCMeta):
    """Interface for verifying TUF payload unwrappers."""

    @staticmethod
    def _validate_signed_type(signed: T, expected: Type[T]) -> None:
        if signed.type != expected.type:
            raise exceptions.RepositoryError(
                f"Expected '{expected.type}', got '{signed.type}'"
            )

    @abc.abstractmethod
    def unwrap(
        self,
        role_cls: Type[T],
        wrapper: bytes,
        delegator: Optional[Delegator] = None,
        role_name: Optional[str] = None,
    ) -> Tuple[T, bytes, Dict[str, Signature]]:
        """Unwrap and verify TUF payload from signature wrapper.

        Verification includes payload type validation, and signature
        verification, if a delegator is passed.

        Arguments:
            role_cls: Class of the role to unwrap.
            wrapper: Raw signature wrapper bytes for to unwrap.
            delegator: Delegator for the role to unwrap and verify. Verification
                is skipped, if no delegator is passed.
            role_name: Name of the role to look up in the delegator. Defaults to
                `role_cls.type``, if not passed.

        Raises:
            tuf.exceptions.RepositoryError: Unexpected payload type

        Returns:
            Tuple: (Deserialized payload, payload bytes, signatures)
        """
        raise NotImplementedError


class MetadataUnwrapper(Unwrapper):
    """Unwrapper implementation for Metadata payloads.

    Order of unwrapping:
    1. Deserialize
    2. Validate inner payload type
    3. Verify signatures

    """

    def unwrap(
        self,
        role_cls: Type[T],
        wrapper: bytes,
        delegator: Optional[Delegator] = None,
        role_name: Optional[str] = None,
    ) -> Tuple[T, bytes, Dict[str, Signature]]:  # noqa: D102
        md = Metadata[T].from_bytes(wrapper)
        self._validate_signed_type(md.signed, role_cls)

        if delegator:
            if role_name is None:
                role_name = role_cls.type

            delegator.verify_delegate(role_name, md.signed_bytes, md.signatures)

        return md.signed, md.signed_bytes, md.signatures
