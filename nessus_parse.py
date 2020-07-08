import csv
import os

import xml.etree.ElementTree as ET

files = [file for file in os.listdir() if '.nessus' in file]
ssl_dont_care = ['SSL Certificate with Wrong Hostname','SSL Certificate Cannot Be Trusted','SSL Certificate Expiry','SSL Self-Signed Certificate']
ip_dict = dict()

for file in files:

    print('Working on {}'.format(file))
    tree = ET.parse(file)
    root = tree.getroot()
    
    for block in root:
        if block.tag == "Report":
            for report_host in block:
                host_properties_dict = dict()
                #tcp_port_dict = dict()
                #udp_port_dict = dict()
                
                for report_item in report_host:
                    cve_list = []
                    port = ''
                    protocol = ''
                    svc_name = ''
                    vulnerability = ''
                    description = ''

                    
                    if report_item.tag == "HostProperties":
                        for host_properties in report_item:
                            host_properties_dict[host_properties.attrib['name']] = host_properties.text
                        
                    else:
                        if report_item.attrib['port'] == '0':
                            pass
                        else:
                            if any(x == report_item.attrib['severity'] for x in ['1','2','3']):
                                vulnerability = report_item.attrib['pluginName']
                                if vulnerability in ssl_dont_care:
                                    pass
                                else:                               
                                    protocol = report_item.attrib['protocol']
                                    port = report_item.attrib['port']
                                    svc_name = report_item.attrib['svc_name']                                    
                                    
                                    for vuln in report_item:
                                        if vuln.tag == 'cve':
                                            cve_list.append(vuln.text)
                                        if vuln.tag == 'description':
                                            description = vuln.text
                                
                                if port == '445':
                                    svc_name = 'smb' 
                            
                            if 'Netstat Portscanner' in report_item.attrib['pluginName']:
                                protocol = report_item.attrib['protocol']
                                port = report_item.attrib['port']
                                svc_name = report_item.attrib['svc_name']
                                
                                if port == '445':
                                    svc_name = 'smb'
                                                           
                        try:
                            ip = host_properties_dict['host-ip']
                        except:
                            ip = report_host.attrib['name']
                        try:
                            fqdn = host_properties_dict['host-fqdn']
                        except:
                            fqdn = '' 
                        try:
                            os = host_properties_dict['operating-system']
                        except:
                            os = ''
                            
                        if '\n' in os:
                            os = ''
                        
                        if port == '':
                            pass
                        else:
                            if ip not in ip_dict.keys():
                                ip_dict[ip] = []
                            
                            all = [fqdn,os,ip,port,protocol,svc_name,vulnerability,"\n".join(cve_list),description]
                            
                            if all not in ip_dict[ip]:
                                if os != '':
                                    if [fqdn,'',ip,port,protocol,svc_name,vulnerability,"\n".join(cve_list),description] in ip_dict[ip]:
                                        ip_dict[ip].remove([fqdn,'',ip,port,protocol,svc_name,vulnerability,"\n".join(cve_list),description])
                                        ip_dict[ip].append(all)
                                    else:
                                        ip_dict[ip].append(all)
                                if os == '':
                                    test = [all[0],all[2],all[3],all[4],all[5]]
                                    isthere = False
                                    for line in ip_dict[ip]:
                                        if [line[0],line[2],line[3],line[4],line[5]] == test and line[1] != '':
                                            isthere = True
                                    if isthere == False:
                                        ip_dict[ip].append(all)
                                    
with open('parsed_nessus.csv', mode='a', newline='') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    for ip in ip_dict.keys():
        for all in ip_dict[ip]:
            csv_writer.writerow(all)
    
                    #for port in tcp_port_dict.keys():
                    #    csv_writer.writerow([fqdn,os,ip,port,tcp_port_dict[port][1],tcp_port_dict[port][0]])        
                    #for port in udp_port_dict.keys():
                    #    csv_writer.writerow([fqdn,os,ip,port,udp_port_dict[port][1],udp_port_dict[port][0]])