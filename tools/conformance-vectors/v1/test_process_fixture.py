"""Keep the packaged sample fixture independent of real production enrollments."""
import unittest
import xml.etree.ElementTree as ET

from run_packaged_process_fixture import enroll_fixture


class ProcessFixtureEnrollmentTests(unittest.TestCase):
    def test_replaces_existing_enrollments_and_preserves_stack_references(self):
        project = ET.fromstring('''<Project><ItemGroup>
          <PackageReference Include="Existing.Contracts" HexalithContracts="true" />
          <PackageReference Include="Metadata.Contracts"><HexalithContracts>TRUE</HexalithContracts></PackageReference>
          <PackageReference Include="Hexalith.EventStore.Contracts" />
          <PackageReference Include="Microsoft.Extensions.Hosting" />
        </ItemGroup></Project>''')
        enroll_fixture(project, 'Synthetic.Contracts')
        references = list(project.iter('PackageReference'))
        self.assertEqual(['Hexalith.EventStore.Contracts', 'Microsoft.Extensions.Hosting',
                          'Synthetic.Contracts'], [item.get('Include') for item in references])
        self.assertEqual('true', references[-1].get('HexalithContracts'))
        enroll_fixture(project, 'Synthetic.Contracts')
        self.assertEqual(3, len(list(project.iter('PackageReference'))))


if __name__ == '__main__':
    unittest.main()
