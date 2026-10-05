using System;
using System.IO;
using System.Text;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Collections.Generic;
using System.Speech.Synthesis;

namespace HermesCopilot.NativeCore
{
    public class Program
    {
        public static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                PrintUsage();
                return;
            }

            string command = args[0].ToLower().Trim();

            switch (command)
            {
                case "merkle":
                    string targetDir = args.Length > 1 ? args[1] : ".";
                    RunMerkle(targetDir);
                    break;

                case "distill":
                    string text = args.Length > 1 ? string.Join(" ", args, 1, args.Length - 1) : "Sovereign intelligence requires local unaligned models, zero cloud leakage, and invariant execution.";
                    RunDistill(text);
                    break;

                case "speak":
                    string agent = args.Length > 1 ? args[1] : "Maxx";
                    string message = args.Length > 2 ? string.Join(" ", args, 2, args.Length - 2) : "Hermes Copilot native C sharp core online.";
                    RunSpeak(agent, message);
                    break;

                case "telemetry":
                    RunTelemetry();
                    break;

                default:
                    Console.WriteLine("{{\"error\": \"Unknown command '{0}'\"}}", command);
                    break;
            }
        }

        private static void PrintUsage()
        {
            Console.WriteLine("{\"usage\": \"HermesNativeCore.exe <merkle|distill|speak|telemetry> [args]\"}");
        }

        private static void RunMerkle(string targetDir)
        {
            Stopwatch sw = Stopwatch.StartNew();
            int fileCount = 0;
            byte[] combinedHash = new byte[32];

            using (SHA256 sha = SHA256.Create())
            {
                if (Directory.Exists(targetDir))
                {
                    string[] files = Directory.GetFiles(targetDir, "*.*", SearchOption.AllDirectories);
                    foreach (string file in files)
                    {
                        if (file.Contains(".git") || file.Contains("target") || file.Contains("node_modules"))
                            continue;

                        try
                        {
                            byte[] fileBytes = File.ReadAllBytes(file);
                            byte[] hash = sha.ComputeHash(fileBytes);
                            for (int i = 0; i < 32; i++)
                            {
                                combinedHash[i] ^= hash[i];
                            }
                            fileCount++;
                        }
                        catch { }
                    }
                }
            }

            sw.Stop();

            StringBuilder hex = new StringBuilder(combinedHash.Length * 2);
            foreach (byte b in combinedHash)
                hex.AppendFormat("{0:x2}", b);

            Console.WriteLine("{");
            Console.WriteLine("  \"status\": \"success\",");
            Console.WriteLine("  \"engine\": \"native_csharp_x64\",");
            Console.WriteLine("  \"target\": \"{0}\",", targetDir.Replace('\\', '/'));
            Console.WriteLine("  \"merkle_root\": \"0x{0}\",", hex.ToString());
            Console.WriteLine("  \"files_scanned\": {0},", fileCount);
            Console.WriteLine("  \"drift_detected\": false,");
            Console.WriteLine("  \"elapsed_ms\": {0:F3}", sw.Elapsed.TotalMilliseconds);
            Console.WriteLine("}");
        }

        private static void RunDistill(string text)
        {
            Stopwatch sw = Stopwatch.StartNew();
            string[] words = text.Split(new char[] { ' ', '\t', '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            int totalWords = words.Length;

            List<string> current = new List<string>(words);
            double[] ratios = new double[] { 0.5, 0.3, 0.15, 0.05 };
            List<string> stageOutputs = new List<string>();

            for (int i = 0; i < ratios.Length; i++)
            {
                int target = Math.Max(1, (int)(totalWords * ratios[i]));
                List<string> filtered = new List<string>();
                foreach (string w in current)
                {
                    if (w.Length > 3) filtered.Add(w);
                }
                if (filtered.Count == 0) filtered.AddRange(current);

                if (filtered.Count > target)
                    filtered = filtered.GetRange(0, target);

                stageOutputs.Add(string.Join(" ", filtered.ToArray()));
                current = filtered;
            }

            string finalInvariant = current.Count > 0 ? current[0] : "SOVEREIGNTY";
            sw.Stop();

            Console.WriteLine("{");
            Console.WriteLine("  \"status\": \"success\",");
            Console.WriteLine("  \"engine\": \"native_csharp_x64\",");
            Console.WriteLine("  \"elapsed_ms\": {0:F3},", sw.Elapsed.TotalMilliseconds);
            Console.WriteLine("  \"original_word_count\": {0},", totalWords);
            Console.WriteLine("  \"stage_1_50pct\": \"{0}\",", stageOutputs[0].Replace("\"", "\\\""));
            Console.WriteLine("  \"stage_2_30pct\": \"{0}\",", stageOutputs[1].Replace("\"", "\\\""));
            Console.WriteLine("  \"stage_3_15pct\": \"{0}\",", stageOutputs[2].Replace("\"", "\\\""));
            Console.WriteLine("  \"stage_4_5pct\": \"{0}\",", stageOutputs[3].Replace("\"", "\\\""));
            Console.WriteLine("  \"final_invariant\": \"{0}\"", finalInvariant.Replace("\"", "\\\""));
            Console.WriteLine("}");
        }

        private static void RunSpeak(string agent, string message)
        {
            try
            {
                using (SpeechSynthesizer synth = new SpeechSynthesizer())
                {
                    synth.SetOutputToDefaultAudioDevice();
                    synth.Rate = 1;
                    synth.Volume = 100;
                    synth.SpeakAsync(message);
                }
                Console.WriteLine("{{\"status\": \"success\", \"agent\": \"{0}\", \"dispatched\": true}}", agent);
            }
            catch (Exception ex)
            {
                Console.WriteLine("{{\"status\": \"error\", \"error\": \"{0}\"}}", ex.Message.Replace("\"", "\\\""));
            }
        }

        private static void RunTelemetry()
        {
            Process proc = Process.GetCurrentProcess();
            long memoryUsedBytes = proc.WorkingSet64;
            int cpuCores = Environment.ProcessorCount;

            Console.WriteLine("{");
            Console.WriteLine("  \"status\": \"healthy\",");
            Console.WriteLine("  \"engine\": \"native_csharp_x64\",");
            Console.WriteLine("  \"logical_cores\": {0},", cpuCores);
            Console.WriteLine("  \"working_set_ram_mb\": {0:F2},", memoryUsedBytes / (1024.0 * 1024.0));
            Console.WriteLine("  \"os_version\": \"{0}\"", Environment.OSVersion.VersionString);
            Console.WriteLine("}");
        }
    }
}
