import ast as pyast

from tide.generators.utils import ProjectFolder
from tide.generators.cpp.infer import TypeInference
from tide.generators.cpp.generator import CppGenerator


class ProjectConverter:
    def __init__(self, root, destination):
        self.project = ProjectFolder(root)
        self.destination = destination

    def run(self):
        import os
        os.makedirs(os.path.join(self.destination, self.project.project_name), exist_ok=True)

        for file in os.listdir(self.project.root):
            with open(os.path.join(self.project.root, file), 'r') as f:
                code = f.read()

            module = pyast.parse(code, filename=file)
            header, impl = CppGenerator(self.project, file).run(module)

            path = os.path.join(self.destination, self.project.project_name)
            with open(os.path.join(path, file.replace('.py', '.cpp')), 'w') as implfile:
                implfile.write(impl)

            with open(os.path.join(path, file.replace('.py', '.h')), 'w') as headerfile:
                headerfile.write(header)


if __name__ == '__main__':
    converter = ProjectConverter(
        'C:/Users/Newton/work/tide/examples/symdiff',
        'C:/Users/Newton/work/tide/examples/out')
    converter.run()

    converter = ProjectConverter(
        'C:/Users/Newton/work/tide/examples/containers',
        'C:/Users/Newton/work/tide/examples/out')
    converter.run()

    # module = pyast.parse("""""".replace('    |', ''))
    #
    # p = ProjectFolder(root='setepenre/work/myproject')
    # header, impl = CppGenerator(p, 'setepenre/work/myproject/add.py').run(module)
    # print(header)
    # print('=============')
    # print(impl)
