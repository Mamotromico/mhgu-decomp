// Disassemble a handful of functions (given as entry-point addresses) and dump
// their instructions as text. Intended for reading compiler idioms early, before
// full auto-analysis: it linearly disassembles from each entry using the program's
// already-selected language (ARM:LE:32:v8 for MHGU).
//
// Usage (headless):
//   analyzeHeadless <projDir> <projName> \
//       -process <program> -noanalysis \
//       -scriptPath <this dir> \
//       -postScript DisasmFunctions.java <addrFile> <outFile> <maxInsns>
//
// <addrFile>: one hex address per line (blank lines / '#' comments ignored).
// @category Soaratorium

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Symbol;

public class DisasmFunctions extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 3) {
            printerr("usage: DisasmFunctions.java <addrFile> <outFile> <maxInsns>");
            return;
        }

        int maxInsns;
        try {
            maxInsns = Integer.parseInt(args[2]);
        } catch (NumberFormatException e) {
            printerr("maxInsns must be an integer: " + args[2]);
            return;
        }
        try (BufferedReader in = new BufferedReader(new FileReader(args[0]));
             PrintWriter out = new PrintWriter(args[1])) {

            String line;
            while ((line = in.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) {
                    continue;
                }
                Address start;
                try {
                    start = toAddr(Long.parseUnsignedLong(
                            line.replaceFirst("^0[xX]", ""), 16));
                } catch (NumberFormatException e) {
                    out.println(";; malformed address: " + line);
                    continue;
                }
                if (start == null || !currentProgram.getMemory().contains(start)) {
                    out.println(";; " + line + "  (no memory)");
                    continue;
                }

                Symbol sym = getSymbolAt(start);
                out.printf(";; entry %s%s%n", start,
                        sym != null ? "  (" + sym.getName() + ")" : "");

                Address cur = start;
                for (int i = 0; i < maxInsns; i++) {
                    if (!currentProgram.getMemory().contains(cur)) {
                        break;
                    }
                    try {
                        if (!disassemble(cur)) {
                            out.printf("  %s  <undisassembled>%n", cur);
                            break;
                        }
                    } catch (Exception e) {
                        out.printf("  %s  <error: %s>%n", cur, e.getMessage());
                        break;
                    }
                    Instruction ins = getInstructionAt(cur);
                    if (ins == null) {
                        out.printf("  %s  <null instruction>%n", cur);
                        break;
                    }
                    StringBuilder sb = new StringBuilder();
                    sb.append(ins.getMnemonicString());
                    int n = ins.getNumOperands();
                    for (int j = 0; j < n; j++) {
                        sb.append(j == 0 ? " " : ", ");
                        sb.append(ins.getDefaultOperandRepresentation(j));
                    }
                    out.printf("  %s  %s%n", cur, sb);
                    cur = ins.getAddress().add(ins.getLength());
                }
                out.println();
            }
        }
        println("DisasmFunctions: wrote " + args[1]);
    }
}
