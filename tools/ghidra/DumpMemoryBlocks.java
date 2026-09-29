// Dump every initialized memory block of the current program to disk.
//
// Purpose: Ghidra's Switch loader decompresses the NSO into an in-memory image.
// This script materializes that image as flat, correctly-addressed binaries so
// they can be inspected with ordinary tools (strings/grep/od) outside Ghidra.
//
// Written in Java (not Python): Ghidra 11+ removed Jython, and Python scripts
// now require the PyGhidra/CPython bridge. A Java GhidraScript compiles itself
// with Ghidra's bundled compiler, so it adds no dependency.
//
// Usage (headless):
//   analyzeHeadless <projDir> <projName> \
//       -process <program> -noanalysis \
//       -scriptPath <this dir> \
//       -postScript DumpMemoryBlocks.java <outputDir>
//
// Output: <outputDir>/<blockname>_<startOffsetHex>.bin for each initialized
// block. Uninitialized blocks (e.g. bss) are skipped.
// @category Soaratorium

import java.io.File;
import java.io.FileOutputStream;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;

public class DumpMemoryBlocks extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            printerr("usage: DumpMemoryBlocks.java <outputDir>");
            return;
        }

        File outdir = new File(args[0]);
        if (!outdir.isDirectory() && !outdir.mkdirs()) {
            printerr("could not create output dir: " + outdir);
            return;
        }

        Memory mem = currentProgram.getMemory();
        for (MemoryBlock block : mem.getBlocks()) {
            if (!block.isInitialized()) {
                println("skip (uninitialized): " + block.getName());
                continue;
            }

            long size = block.getSize();
            String name = block.getName().replace('/', '_');
            File out = new File(outdir, String.format("%s_%08x.bin", name,
                    block.getStart().getOffset()));

            byte[] data = new byte[(int) size];
            block.getBytes(block.getStart(), data);
            try (FileOutputStream fos = new FileOutputStream(out)) {
                fos.write(data);
            }
            println(String.format("wrote %s (0x%x bytes)", out.getPath(), size));
        }
    }
}
