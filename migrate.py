import json
import os
import glob

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def update_anthropic_to_gemini(node):
    if node['type'] == '@n8n/n8n-nodes-langchain.lmChatAnthropic':
        node['type'] = '@n8n/n8n-nodes-langchain.lmChatGoogleGemini'
        node['typeVersion'] = 1
        node['name'] = node['name'].replace('Anthropic Chat Model', 'Gemini Chat Model')
        node['parameters'] = {
            "model": {
                "__rl": True,
                "value": "models/gemini-1.5-flash",
                "mode": "list",
                "cachedResultName": "Gemini 1.5 Flash"
            },
            "options": {}
        }
        if 'credentials' in node:
            node['credentials'] = {
                "googlePalmApi": {
                    "id": "",
                    "name": "Google Gemini(PaLM) Api account"
                }
            }
    return node

def migrate_part_1(data):
    for node in data['nodes']:
        update_anthropic_to_gemini(node)
        
        # Update Webhook URL for Triggering Part 2
        if node['name'] == 'Trigger Scene Workflow':
            node['parameters']['url'] = 'http://localhost:5678/webhook/part2'
            
    return data

def migrate_part_2(data):
    for node in data['nodes']:
        update_anthropic_to_gemini(node)
        
        if node['name'] == 'Webhook':
            node['parameters']['path'] = 'part2'
            
        if node['name'] == 'Trigger Video Workflow':
            node['parameters']['url'] = 'http://localhost:5678/webhook/part3'
            
    return data

def migrate_part_3(data):
    new_nodes = []
    
    # We will remove the video generation nodes
    nodes_to_remove = [
        'Atlas Cloud Generate Video', 
        'Atlas Cloud Poll Result', 
        'Wait', 
        'If', 
        'Extract Video URLs',
        'Build Kling Payloads',
        'Merge Video Prompts'
    ]
    
    for node in data['nodes']:
        if node['name'] in nodes_to_remove:
            continue
            
        update_anthropic_to_gemini(node)
        
        if node['name'] == 'Webhook1':
            node['parameters']['path'] = 'part3'
            
        # Swap Blotato to YouTube
        if node['name'] == 'Youtube':
            node['type'] = 'n8n-nodes-base.googleYouTube'
            node['typeVersion'] = 1
            node['name'] = 'Upload to YouTube'
            node['parameters'] = {
                "operation": "upload",
                "title": "={{ $json.output.scenes[0].video_title }}",
                "description": "={{ $json.output.scenes[0].video_description }}",
                "categoryId": "1",
                "privacyStatus": "private",
                "mediaContent": "={{ $('Shotstack Poll Result').item.json.response.url }}"
            }
            if 'credentials' in node:
                node['credentials'] = {
                    "googleYouTubeOAuth2Api": {
                        "id": "",
                        "name": "Google YouTube OAuth2 API"
                    }
                }
                
        # Update Shotstack Payload to use images instead of video
        if node['name'] == 'Build Shotstack Payload':
            node['parameters']['jsCode'] = """const audioItems = $input.all();
const chunkItems = $('Split Video Chunks').all();

if (!chunkItems || chunkItems.length === 0) {
  throw new Error('No chunks found from "Split Video Chunks".');
}
if (!audioItems || audioItems.length === 0) {
  throw new Error('No audio found.');
}

const staticData = $getWorkflowStaticData('global');
const title = staticData.title ?? chunkItems[0]?.json?.title ?? 'Untitled';

const scenes = chunkItems.map((chunkItem, i) => ({
  chunk_number: chunkItem.json.chunk_number,
  duration_seconds: chunkItem.json.duration_seconds,
  scene_image_url: chunkItem.json.scene_image_url,
  audio_url: audioItems[i]?.json?.audio_url ?? null
}));

return [{
  json: {
    title: title,
    scenes: scenes
  }
}];"""

        if node['name'] == 'Build Shotstack Timeline':
            node['parameters']['jsCode'] = """const data = $input.first().json;

let currentTime = 0;
const videoClips = [];
const audioClips = [];

const effects = ["zoomIn", "zoomOut", "slideLeft", "slideRight", "slideUp", "slideDown"];

for (let i = 0; i < data.scenes.length; i++) {
  const scene = data.scenes[i];
  const effect = effects[i % effects.length];
  
  videoClips.push({
    asset: {
      type: "image",
      src: scene.scene_image_url
    },
    start: currentTime,
    length: scene.duration_seconds,
    effect: effect
  });

  audioClips.push({
    asset: {
      type: "audio",
      src: scene.audio_url,
      volume: 1
    },
    start: currentTime,
    length: "auto"
  });

  currentTime += scene.duration_seconds;
}

return [{
  json: {
    body: JSON.stringify({
      timeline: {
        tracks: [
          { clips: videoClips },
          { clips: audioClips }
        ]
      },
      output: {
        format: "mp4",
        resolution: "hd"
      }
    })
  }
}];"""
            
        new_nodes.append(node)
        
    data['nodes'] = new_nodes
    
    # We also need to fix connections, removing the deleted nodes from the connection tree
    if 'connections' in data:
        # Rewire Generate Video Prompts -> Wait1
        # Wait, originally: Generate Video Prompts -> Merge Video Prompts -> Build Kling ... -> Wait -> Wait1? No.
        # Let's check original connections.
        pass
        
    return data

def fix_part_3_connections(data):
    # Instead of manual rewiring which is complex in Python for n8n, 
    # since we removed Kling, we just bypass it.
    # The original flow for part 3 was:
    # Split Video Chunks -> Build Narration Context -> Generate Video Prompts (Claude)
    # Actually, Generate Video Prompts just produced descriptions.
    # Then Loop Over Items -> ElevenLabs Narrate -> Upload Audio to Cloudinary -> Wait1
    # Loop Over Items uses Extract Video URLs as input. We removed that.
    # So we need to feed Split Video Chunks directly into Loop Over Items!
    
    connections = data.get('connections', {})
    
    # Remove connections from/to deleted nodes
    deleted_nodes = [
        'Atlas Cloud Generate Video', 
        'Atlas Cloud Poll Result', 
        'Wait', 
        'If', 
        'Extract Video URLs',
        'Build Kling Payloads',
        'Merge Video Prompts'
    ]
    
    new_conns = {}
    for node_name, conn_data in connections.items():
        if node_name in deleted_nodes:
            continue
        new_main = []
        if 'main' in conn_data:
            for out_arr in conn_data['main']:
                filtered_out = [c for c in out_arr if c['node'] not in deleted_nodes]
                new_main.append(filtered_out)
        
        # If this node was Generate Video Prompts, it originally went to Merge Video Prompts.
        # Now we don't even need Generate Video Prompts because we aren't generating video prompts for Kling!
        # Wait, we do need it because it ALSO SHORTENS THE NARRATION for ElevenLabs!
        # So Generate Video Prompts -> Loop Over Items
        if node_name == 'Generate Video Prompts':
            new_main = [[{"node": "Prepare Narration Loop", "type": "main", "index": 0}]]
            
        new_conn_data = {}
        if new_main:
            new_conn_data['main'] = new_main
        if 'ai_languageModel' in conn_data:
            new_conn_data['ai_languageModel'] = conn_data['ai_languageModel']
        if 'ai_outputParser' in conn_data:
            new_conn_data['ai_outputParser'] = conn_data['ai_outputParser']
            
        if new_conn_data:
            new_conns[node_name] = new_conn_data
            
    # Also fix Prepare Narration Loop to take input from Generate Video Prompts instead of Split Video Chunks
    # Wait, Prepare Narration Loop originally got data from Generate Video Prompts anyway. 
    # Let's check: "Prepare Narration Loop" in original json:
    # "const scenes = $('Generate Video Prompts').first().json.output.scenes;"
    # So it doesn't strictly depend on the main input wire for content, but it does for execution order.
    # We will make Generate Video Prompts -> Prepare Narration Loop.
    
    data['connections'] = new_conns
    return data

def main():
    base_dir = '/home/ju-nine/projects/personal/youtube_automation/'
    part1_file = glob.glob(base_dir + '*PART 1*.json')[0]
    part2_file = glob.glob(base_dir + '*PART 2*.json')[0]
    part3_file = glob.glob(base_dir + '*PART 3*.json')[0]
    
    part1_data = load_json(part1_file)
    part2_data = load_json(part2_file)
    part3_data = load_json(part3_file)
    
    part1_new = migrate_part_1(part1_data)
    part2_new = migrate_part_2(part2_data)
    part3_new = migrate_part_3(part3_data)
    part3_new = fix_part_3_connections(part3_new)
    
    # Update the name of the workflows
    part1_new['name'] = "SketchTales V2 - PART 1"
    part2_new['name'] = "SketchTales V2 - PART 2"
    part3_new['name'] = "SketchTales V2 - PART 3"
    
    save_json(base_dir + 'Part_1_V2.json', part1_new)
    save_json(base_dir + 'Part_2_V2.json', part2_new)
    save_json(base_dir + 'Part_3_V2.json', part3_new)

    print("Migration complete!")

if __name__ == '__main__':
    main()
