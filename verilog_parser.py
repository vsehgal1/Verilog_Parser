# FUNCTION TO RETRIEVE CIRCUIT: getRawCircuit()
# FUNCTION TO COUNT TOTAL INSTANCES/MODULES: totalInstances(MODU)
# When testing please remove all new lines in instance definition.


import re
import copy

# class to keep track of inner modules inside each module. 
# Points Parent module to child module which is also stored in circuit {} dictionary 
# and can be accessed through it.
class InnerModule:
    def __init__(self, module, instance, input_port, input_net, output_port, output_net):
        super().__init__()
        self.module = module
        self.instance = instance
        self.input_port = input_port
        self.input_net = input_net
        self.output_port = output_port
        self.output_net = output_net

# class to keep track of inner primitives inside each module
class Primitives:
    def __init__(self, primitive, instance, input_port, input_net, output_port, output_net):
        super().__init__()
        self.primitive = primitive
        self.instance = instance
        self.input_port = input_port
        self.input_net = input_net
        self.output_port = output_port
        self.output_net = output_net


# Main module class
class Module:
    def __init__(self, name='', inputs=None, outputs=None, wires=None, inner_modules=None, inner_primitives=None):
        # super().__init__()
        self.name = name
        if inputs is None:
            self.inputs = {}
        if outputs is None:
            self.outputs = {}
        if wires is None:
            self.wires = {}
        if inner_modules is None:
            self.inner_modules = []
        if inner_primitives is None:
            self.inner_primitives = []

    def addOutput(self, port):
        if len(port) == 1:
            self.outputs[port[0][:-1]] = [0, 0]
        else:
            bits = re.search('\d+:\d+', port[0])[0].split(':')
            self.outputs[port[-1][:-1]] = bits

    def addInputs(self, port):
        if len(port) == 1:
            self.inputs[port[0][:-1]] = [0, 0]
        else:
            bits = re.search('\d+:\d+', port[0])[0].split(':')
            self.inputs[port[-1][:-1]] = bits

    def addWire(self, wire):
        if len(wire) == 1:
            self.wires[wire[0][:-2]] = [0, 0]
        else:
            bits = re.search('\d+:\d+', wire[0])[0].split(':')
            self.wires[wire[-1][:-2]] = bits

    def addInnerModule(self, module, name, ports):
        input_ports = self.getPorts('input', ports)
        output_ports = self.getPorts('output', ports)
        input_net = self.getNet('input', ports)
        output_net = self.getNet('output', ports)
        self.inner_modules.append(InnerModule(
            module, name, input_ports, input_net, output_ports, output_net))

    def addInnerPrimitive(self, primitive, name, ports):
        inputP = self.getPrimitiveNet('input', ports)
        input_ports, input_net = inputP[0], inputP[1]
        outputP = self.getPrimitiveNet('output', ports)
        output_ports, output_net = outputP[0], outputP[1]
        self.inner_primitives.append(Primitives(
            primitive, name, input_ports, input_net, output_ports, output_net))

    def getName(self):
        return self.name

    def getPrimitiveNet(self, pType, ports):
        ports = [i[1:] for i in ports]
        ports = [i.split('(') for i in ports]
        if pType == 'input':
            port_list = [i for i in ports if 'out' not in i[1]]
        else:
            port_list = [i for i in ports if 'out' in i[1]]
        pPort = [i[0] for i in port_list]
        port_list = [i[1] for i in port_list]
        port_net = []
        for i in port_list:
            i = i.replace(')', '')
            i = i.replace(';', '')
            i = i.replace('\n', '')
            port_net.append(i)
        return (pPort, port_net)

    def getPorts(self, pType, ports):
        port_string = ' '.join(ports)
        if pType == 'input':
            input_ports = re.findall('(in\d*\w*\(|data\()', port_string)
            input_ports = [i[:-1] for i in input_ports]
            return input_ports
        else:
            outputPorts = re.findall('(out\d*\w*\(|data\()', port_string)
            outputPorts = [i[:-1] for i in outputPorts]
            return outputPorts

    def getNet(self, pType, ports):
        if pType == 'input':
            port_net = [i for i in ports if 'in' in i or 'data' in i]
        else:
            port_net = [i for i in ports if 'out' in i]
        port_net = [i[1:-1] for i in port_net]
        port_net = [i.split('(')[1].split(')')[0] for i in port_net]
        return port_net

    def getInnerModule(self):
        return self.inner_modules

    def getPrimitive(self):
        return self.inner_primitives


class Circuit:
    def __init__(self, verilog, circuit=None):
        super().__init__()
        self.verilog = verilog
        if circuit is None:
            self.circuit = {}
        self.parse()

    def parse(self):
        primitives = ['invN\d+', 'nand\d+N\d+', 'nor\d+N\d+', 'nand\d+N\d+']
        combined = "(" + ")|(".join(primitives) + ")"
        modules = []
        temp = []
        for line in self.verilog.readlines():
            if (line[0] == '/' and line[1] == '/') or line == '\n':
                continue
            if 'endmodule' in line:
                temp.append(line)
                modules.append(temp)
                temp = []
            else:
                temp.append(line)
        # store each module
        for module in modules:
            declare = module[0].split(' ')
            new_module = Module(declare[1])
            for line in module[1:]:
                tokens = line.split(' ')
                tokens = list(filter(('').__ne__, tokens))
                if 'endmodule' in tokens:
                    self.circuit[new_module.getName()] = new_module
                elif 'output' in tokens:
                    new_module.addOutput(tokens[1:])
                elif 'input' in tokens:
                    new_module.addInputs(tokens[1:])
                elif 'wire' in tokens:
                    new_module.addWire(tokens[1:])
                elif re.match(combined, tokens[0]):
                    new_module.addInnerPrimitive(
                        tokens[0], tokens[1], tokens[2:])
                else:
                    new_module.addInnerModule(tokens[0], tokens[1], tokens[2:])
            new_module = None

    def getRawCircuit(self):
        return self.circuit

    # Function to count all instances of modules/primitives
    def totalInstances(self, module):
        
        #reference to current module
        cur_module = self.circuit[module]
        module_count = {}
        inner_module_count = None

        # helper function to recurse through each module and adding all its modules to module_count
        def helper(head, acc):
            for i in self.circuit[head].getInnerModule():
                if i.module not in acc:
                    acc[i.module] = 1
                    # calling here for optimization. Only recurse once!
                    helper(i.module, acc)
                else:
                    acc[i.module] += 1
            for i in self.circuit[head].getPrimitive():
                if i.primitive not in acc:
                    acc[i.primitive] = 1
                else:
                    acc[i.primitive] += 1
            return acc

        for i in cur_module.getInnerModule():
            if i.module not in module_count:
                module_count[i.module] = 1
                # if more instance definition of same module we simply add whatever we got from the helper
                # instead of recursing again
                inner_module_count = helper(i.module, {})
                temp = copy.deepcopy(inner_module_count)
            else:
                for key in inner_module_count:
                    inner_module_count[key] += temp[key]
                module_count[i.module] += 1

        for i in cur_module.getPrimitive():
            if i.primitive not in module_count:
                module_count[i.primitive] = 1
            else:
                module_count[i.primitive] += 1
        # if we did use recursion we add whatever we got through the helper to our main 
        # module count dictionary
        if inner_module_count:
            for key in inner_module_count:
                if key in module_count:
                    module_count[key] += inner_module_count[key]
                else:
                    module_count[key] = inner_module_count[key]
        return module_count
        


def main():

    # ALL OPERATIONS GO INSIDE THIS BLOCK!
    with open('TopCell.v', 'r') as reader:
        circuit = Circuit(reader)

        # FUNCTION: getRawCircuit()
        # this function will return a dictionary of circuit modules
        # structure: {'Module_Name' => 'Module_Object'}
        # Module_Object is a class conataining all the relevant properties like
        # input and output pins and ports, wires, instances
        print(circuit.getRawCircuit)

        # FUNCTION: circuit.totalInstances(MODULE_NAMe)
        # this function will find all occuerences. It recursively goes through each module
        print(circuit.totalInstances('TopCell'))




if __name__ == "__main__":
    main()