from unittest import TestCase

from autosubmit.job.job import Job
from autosubmit.job.job_common import Status


class TestJob(TestCase):
    def setUp(self):
        self.jobs = list()
        self.jobs.append(Job('whatever', 0, Status.UNKNOWN, 0))
        self.jobs.append(Job('whatever', 1, Status.UNKNOWN, 0))
        self.jobs.append(Job('whatever', 2, Status.UNKNOWN, 0))
        self.jobs.append(Job('whatever', 3, Status.UNKNOWN, 0))
        self.jobs.append(Job('whatever', 4, Status.UNKNOWN, 0))

        create_relationship(self.jobs[0], self.jobs[1])
        create_relationship(self.jobs[0], self.jobs[2])
        create_relationship(self.jobs[1], self.jobs[3])
        create_relationship(self.jobs[1], self.jobs[4])
        create_relationship(self.jobs[2], self.jobs[3])
        create_relationship(self.jobs[2], self.jobs[4])

    def test_is_ancestor_works_well(self):
        self.check_ancestors_array(self.jobs[0], [False, False, False, False, False])
        self.check_ancestors_array(self.jobs[1], [False, False, False, False, False])
        self.check_ancestors_array(self.jobs[2], [False, False, False, False, False])
        self.check_ancestors_array(self.jobs[3], [True, False, False, False, False])
        self.check_ancestors_array(self.jobs[4], [True, False, False, False, False])

    def test_is_parent_works_well(self):
        self.check_parents_array(self.jobs[0], [False, False, False, False, False])
        self.check_parents_array(self.jobs[1], [True, False, False, False, False])
        self.check_parents_array(self.jobs[2], [True, False, False, False, False])
        self.check_parents_array(self.jobs[3], [False, True, True, False, False])
        self.check_parents_array(self.jobs[4], [False, True, True, False, False])

    def test_remove_redundant_parents_works_well(self):
        # Adding redundant relationships
        create_relationship(self.jobs[0], self.jobs[3])
        create_relationship(self.jobs[0], self.jobs[4])
        # Checking there are redundant parents
        self.assertEqual(3, len(self.jobs[3].parents))
        self.assertEqual(3, len(self.jobs[4].parents))
        # Treating the redundant parents
        self.jobs[3].remove_redundant_parents()
        self.jobs[4].remove_redundant_parents()
        # Checking there aren't redundant parents
        self.assertEqual(2, len(self.jobs[3].parents))
        self.assertEqual(2, len(self.jobs[4].parents))

    def check_ancestors_array(self, job, assertions):
        for i in range(len(self.jobs)):
            self.assertEqual(assertions[i], job.is_ancestor(self.jobs[i]))

    def check_parents_array(self, job, assertions):
        for i in range(len(self.jobs)):
            self.assertEqual(assertions[i], job.is_parent(self.jobs[i]))


def create_relationship(parent, child):
    parent.children.add(child)
    child.parents.add(parent)
