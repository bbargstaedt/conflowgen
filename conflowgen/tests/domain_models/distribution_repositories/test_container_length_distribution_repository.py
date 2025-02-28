import unittest

from conflowgen.domain_models.distribution_models.container_length_distribution import ContainerLengthDistribution
from conflowgen.domain_models.distribution_repositories.container_length_distribution_repository import \
    ContainerLengthDistributionRepository, ContainerLengthProportionsUnequalOneException, \
    ContainerLengthProportionOutOfRangeException, ContainerLengthMissing
from conflowgen.domain_models.distribution_seeders import container_length_distribution_seeder
from conflowgen.domain_models.data_types.container_length import ContainerLength
from conflowgen.tests.substitute_peewee_database import setup_sqlite_in_memory_db


class TestContainerLengthDistributionRepository(unittest.TestCase):

    def setUp(self) -> None:
        """Create container database in memory"""
        sqlite_db = setup_sqlite_in_memory_db()
        sqlite_db.create_tables([
            ContainerLengthDistribution
        ])
        container_length_distribution_seeder.seed()

    def test_known_values_via_get_distribution(self):
        """Must be updated once the seeded values change"""
        distribution = ContainerLengthDistributionRepository.get_distribution()
        self.assertEqual(distribution[ContainerLength.twenty_feet], 0.4)
        self.assertEqual(distribution[ContainerLength.forty_feet], 0.6)
        self.assertEqual(distribution[ContainerLength.forty_five_feet], 0)
        self.assertEqual(distribution[ContainerLength.other], 0)

    def test_container_lengths_in_distribution(self):
        container_length_distribution = ContainerLengthDistributionRepository.get_distribution()
        self.assertIn(ContainerLength.twenty_feet, container_length_distribution.keys())
        self.assertIn(ContainerLength.forty_feet, container_length_distribution.keys())
        self.assertIn(ContainerLength.forty_five_feet, container_length_distribution.keys())

    def test_distribution_loader_sums_up_to_one_per_container_length(self):
        container_length_distribution = ContainerLengthDistributionRepository.get_distribution()
        sum_of_all_fractions = sum(container_length_distribution.values())
        self.assertAlmostEqual(
            sum_of_all_fractions,
            1,
            msg=f"All probabilities must sum to 1, but you only achieved {sum_of_all_fractions}"
        )

    def test_distribution_loader_values_range_between_zero_to_one(self):
        container_length_distribution = ContainerLengthDistributionRepository.get_distribution()
        for container_length in ContainerLength:
            proportion = container_length_distribution[container_length]
            self.assertGreaterEqual(proportion, 0)
            self.assertLessEqual(proportion, 1)

    def test_happy_path(self) -> None:
        ContainerLengthDistributionRepository.set_distribution(
            {
                ContainerLength.twenty_feet: 0.5,
                ContainerLength.forty_feet: 0.5,
                ContainerLength.forty_five_feet: 0,
                ContainerLength.other: 0
            }
        )

    def test_set_twice(self) -> None:
        ContainerLengthDistributionRepository.set_distribution(
            {
                ContainerLength.twenty_feet: 0.5,
                ContainerLength.forty_feet: 0.5,
                ContainerLength.forty_five_feet: 0,
                ContainerLength.other: 0
            }
        )
        ContainerLengthDistributionRepository.set_distribution(
            {
                ContainerLength.twenty_feet: 0.5,
                ContainerLength.forty_feet: 0.5,
                ContainerLength.forty_five_feet: 0,
                ContainerLength.other: 0
            }
        )

    def test_set_container_lengths_with_missing_lengths(self) -> None:
        with self.assertRaises(ContainerLengthMissing):
            ContainerLengthDistributionRepository.set_distribution(
                {
                    ContainerLength.twenty_feet: 1
                }
            )

    def test_set_container_lengths_with_wrong_proportions(self) -> None:
        with self.assertRaises(ContainerLengthProportionOutOfRangeException):
            ContainerLengthDistributionRepository.set_distribution(
                {
                    ContainerLength.twenty_feet: -1,  # the malicious entry
                    ContainerLength.forty_feet: 1,
                    ContainerLength.forty_five_feet: 0.5,
                    ContainerLength.other: 0.5
                }
            )

    def test_set_container_lengths_which_do_not_add_up_to_one(self) -> None:
        with self.assertRaises(ContainerLengthProportionsUnequalOneException):
            ContainerLengthDistributionRepository.set_distribution(
                {
                    ContainerLength.twenty_feet: 0.9,  # this and...
                    ContainerLength.forty_feet: 0.9,   # ...this are already more than 1
                    ContainerLength.forty_five_feet: 0,
                    ContainerLength.other: 0
                }
            )
